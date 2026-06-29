# Modelo de Dados

O sistema usa dois bancos PostgreSQL separados: um central (nuvem) e um edge (ônibus).

---

## Banco Central (PostgreSQL + pgvector)

### Diagrama Entidade-Relacionamento

```
users
  id (PK)
  email
  full_name
  hashed_password
  role (ADMIN)
  created_at

passengers
  id (PK)
  full_name
  document_number (UNIQUE)
  status (ACTIVE | BLOCKED)
  created_at
  updated_at

face_embeddings
  id (PK)
  passenger_id (FK → passengers)
  embedding    VECTOR(512)       ← pgvector
  model_name
  model_version
  quality_score
  liveness_score
  active        BOOLEAN
  created_at
  revoked_at

tickets
  id (PK)
  passenger_id (FK → passengers)
  ticket_type
  status (ACTIVE | EXPIRED | CANCELLED)
  valid_from
  valid_until
  created_at
  updated_at

boarding_validations
  id (PK)
  external_id    (UUID gerado no edge, UNIQUE — idempotência)
  bus_id
  route_id
  passenger_id (FK → passengers, nullable — DENIED sem ID)
  ticket_id    (FK → tickets, nullable)
  status       (AUTHORIZED | DENIED_*)
  confidence_score
  similarity_distance
  reason_code
  is_offline   BOOLEAN
  captured_at
  synced_at
  created_at

sync_states
  id (PK)
  device_id    (UNIQUE)
  last_pull_cursor
  last_push_cursor
  updated_at
```

### Índices relevantes

```sql
-- Busca vetorial no central (cosine similarity)
CREATE INDEX ON face_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Filtros frequentes
CREATE INDEX ON face_embeddings (passenger_id, active);
CREATE INDEX ON tickets (passenger_id, status, valid_until);
CREATE INDEX ON boarding_validations (captured_at DESC);
CREATE INDEX ON boarding_validations (external_id);
```

---

## Banco Edge (PostgreSQL — cache local)

Subset mínimo necessário para operar sem internet.

```
local_passengers
  id (PK, UUID — mesmo do central)
  full_name
  document_number
  status
  synced_at

local_face_embeddings
  id (PK, UUID — mesmo do central)
  passenger_id (FK → local_passengers)
  embedding    BYTEA                 ← NumPy array serializado
  model_name
  model_version
  active       BOOLEAN
  synced_at

local_tickets
  id (PK, UUID — mesmo do central)
  passenger_id (FK → local_passengers)
  ticket_type
  status
  valid_from
  valid_until
  synced_at

local_validation_logs
  id (PK, UUID — gerado no edge)
  bus_id
  route_id
  passenger_id (nullable)
  ticket_id    (nullable)
  status
  confidence_score
  similarity_distance
  reason_code
  is_offline   BOOLEAN
  captured_at
  synced_to_central  BOOLEAN DEFAULT false

sync_states
  id (PK)
  bus_id       (UNIQUE)
  last_pull_cursor
  updated_at
```

### Diferenças em relação ao banco central

| Aspecto | Central | Edge |
|---|---|---|
| Extensão vetorial | pgvector (`VECTOR(512)`) | NumPy (`BYTEA`) |
| Busca vetorial | SQL via pgvector | Python puro (distância cosseno) |
| Dados de passageiro | Completo | Apenas campos necessários para validação |
| Histórico | Completo | Apenas logs não sincronizados |
| Migrations | Alembic (8 migrations) | Alembic (separado) |

---

## Política de Dados Biométricos (LGPD)

Os embeddings faciais são dados biométricos sensíveis (LGPD Art. 5, XI).

- **Coleta:** somente com imagem fornecida explicitamente pelo operador admin no cadastro.
- **Armazenamento:** embedding numérico, não a imagem original — minimização de dados.
- **Revogação:** `POST /passengers/{id}/biometrics/revoke` marca o embedding como `active=false` e registra `revoked_at`. No próximo pull, o edge recebe `active=false` e para de usar o embedding.
- **Exclusão do passageiro:** `DELETE /passengers/{id}` remove os embeddings associados via cascade.
- **Retenção no edge:** o sync-worker só mantém embeddings com `active=true` no cache local.

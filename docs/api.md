# Referência de API

Documentação interativa disponível em produção:
- **Central API:** https://bfv-central-api.up.railway.app/docs
- **Edge API:** https://edge-api-production-8af2.up.railway.app/docs

Localmente: `http://localhost:8000/docs` e `http://localhost:8001/docs`

---

## Autenticação

### Central API — Usuários administrativos

```
POST /auth/login
Content-Type: application/json

{ "email": "admin@example.com", "password": "senha" }

→ 200 { "access_token": "...", "token_type": "bearer" }
```

Endpoints protegidos: header `Authorization: Bearer <token>`

### Central API — Dispositivos edge

Endpoints `/sync/*` protegidos por `X-Device-Key: <EDGE_SYNC_API_KEY>` (shared secret por dispositivo).

---

## Central API — Endpoints

### Auth

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/login` | Login de admin, retorna JWT |
| POST | `/auth/users` | Cria usuário admin (requer JWT de admin) |

### Passageiros

| Método | Rota | Descrição |
|---|---|---|
| GET | `/passengers` | Lista passageiros (paginado) |
| POST | `/passengers` | Cria passageiro |
| GET | `/passengers/{id}` | Detalhe do passageiro |
| PUT | `/passengers/{id}` | Atualiza passageiro |
| DELETE | `/passengers/{id}` | Remove passageiro |

### Biometria

| Método | Rota | Descrição |
|---|---|---|
| POST | `/passengers/{id}/biometrics/enroll` | Cadastra biometria (upload de imagem) |
| GET | `/passengers/{id}/biometrics` | Lista embeddings do passageiro |
| POST | `/passengers/{id}/biometrics/revoke` | Revoga embedding ativo |

O endpoint de enroll envia a imagem para o `vision-service`, recebe o embedding 512-d e persiste com metadados do modelo (nome, versão, quality_score).

### Passagens

| Método | Rota | Descrição |
|---|---|---|
| GET | `/tickets` | Lista passagens |
| POST | `/tickets` | Cria passagem |
| GET | `/tickets/{id}` | Detalhe da passagem |
| PUT | `/tickets/{id}` | Atualiza passagem |
| DELETE | `/tickets/{id}` | Remove passagem |

### Validações

| Método | Rota | Descrição |
|---|---|---|
| GET | `/validations` | Lista logs de embarque sincronizados |
| GET | `/validations/{id}` | Detalhe de uma validação |
| GET | `/validations/stats` | Contagem por status (dashboard) |

### Sync (X-Device-Key)

| Método | Rota | Descrição |
|---|---|---|
| POST | `/sync/pull` | Edge puxa passageiros/embeddings/tickets atualizados |
| POST | `/sync/push` | Edge envia logs de validação |
| POST | `/sync/ack` | Edge confirma cursor após pull |

### Sync (JWT admin)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/sync/devices` | Lista dispositivos com last_pull_at / last_push_at |

### Health

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Status da API e banco |

### Métricas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/metrics` | Métricas Prometheus (prometheus-fastapi-instrumentator) |

---

## Edge API — Endpoints

### Validação de Embarque

```
POST /validate-boarding
Content-Type: multipart/form-data

Campos:
  file: imagem (JPEG/PNG) capturada pela câmera

→ 200 {
    "status": "AUTHORIZED" | "DENIED_*",
    "passenger_name": "...",
    "confidence_score": 0.91,
    "similarity_distance": 0.18,
    "reason_code": "..."
  }
```

Status possíveis:
- `AUTHORIZED`
- `DENIED_NO_ACTIVE_TICKET`
- `DENIED_LOW_CONFIDENCE`
- `DENIED_FACE_NOT_FOUND`
- `DENIED_SPOOF_SUSPECTED`
- `DENIED_PASSENGER_BLOCKED`

### Health

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Status da API, banco, conectividade central |

### Métricas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/metrics` | Métricas Prometheus |

---

## Vision Service — Endpoints (interno)

Chamado apenas pela `central-api` e `edge-api`. Não exposto publicamente.

```
POST /embeddings/generate
Content-Type: multipart/form-data

Campos:
  file: imagem facial

→ 200 {
    "embedding": [0.12, -0.34, ...],  // 512 floats
    "quality_score": 0.87,
    "liveness_score": 0.92,
    "model_name": "arcface",
    "model_version": "buffalo_l"
  }
```

Erros comuns:
- `422` — nenhuma face detectada na imagem
- `422` — qualidade abaixo do threshold mínimo
- `422` — liveness score abaixo do threshold (suspeita de foto/spoof)

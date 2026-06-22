# Edge API

API local, executada a bordo de cada ônibus: valida o embarque (RF07/RF08/
RF09) contra um cache local de passageiros/embeddings/tickets, sem depender
da `central-api` no caminho crítico — é isso que torna o sistema
offline-first (RFC 3.2) e não apenas "tolerante a queda".

## Stack

- **FastAPI** — camada HTTP.
- **SQLAlchemy (async) + asyncpg** — `postgres-edge`, banco local da
  própria instância (não compartilhado com a `central-api`).
- **Alembic** — migrations locais, independentes das do `central-api`.
- **NumPy** — distância de cosseno pura para o matching local (sem
  pgvector: banco local não tem a extensão instalada).
- **httpx** — chamadas ao `vision-service` local e ping de
  conectividade ao `central-api`.

## Por que existe um banco separado (`postgres-edge`)

Cada ônibus precisa decidir embarque mesmo sem rede até a central. O
`edge-api` mantém uma cópia local (`LocalPassenger`, `LocalFaceEmbedding`,
`LocalTicket`) sincronizada periodicamente pelo `sync-worker` via
`central-api`'s `/sync/pull`. Os IDs dessas tabelas **não são gerados
localmente** — vêm do registro central, então as colunas `id` não têm
`default=uuid.uuid4`.

### Propagação de revogação biométrica (`LocalFaceEmbedding.active`)

`local_face_embeddings` tem uma coluna `active` (migration `20260622_0006`)
que espelha `FaceEmbedding.active` da `central-api`. Antes dessa migration,
`EmbeddingCacheRepository.list_active()` devolvia a tabela inteira sem
filtro nenhum, partindo da premissa de que "central só sincroniza
embeddings ativos" — premissa falsa para pulls incrementais (ver
`central-api.md`, seção "Propagação de status no pull incremental"): um
embedding revogado (reenrollment ou bloqueio) nunca mais aparecia em
nenhum pull futuro, então a versão antiga (já revogada) ficava no cache
local indefinidamente e continuava autorizando embarque offline. Agora
`list_active()` filtra `WHERE active = true`, e o `sync-worker` grava o
campo `active` que vem em cada `EmbeddingSyncItem` — inclusive quando ele
é `False`.

## Pipeline de validação (`app/modules/validation/service.py`)

```
imagem -> vision-service local (detect_and_embed)
  -> sem rosto?              -> DENIED_FACE_NOT_FOUND
  -> spoof_suspected=true?   -> DENIED_SPOOF_SUSPECTED
  -> quality_score baixo?    -> DENIED_LOW_CONFIDENCE (LOW_QUALITY)
  -> busca o vizinho mais próximo entre os embeddings cacheados (NumPy)
  -> distância > limiar?     -> DENIED_LOW_CONFIDENCE (NO_MATCH_WITHIN_THRESHOLD)
  -> passageiro bloqueado?   -> DENIED_PASSENGER_BLOCKED
  -> sem ticket ativo?       -> DENIED_NO_ACTIVE_TICKET
  -> caso contrário          -> AUTHORIZED
```

Cada tentativa é persistida em `LocalValidationLog`, com `synced_at NULL`
funcionando como fila de saída para o `sync-worker` (sem necessidade de
uma tabela de outbox separada). Limiares (`MIN_FACE_QUALITY_SCORE`,
`MAX_SIMILARITY_DISTANCE`) são configuráveis e espelham os mesmos campos
da `central-api`, para que o comportamento seja consistente entre
cadastro central e validação local.

## Endpoints

- `POST /local/validate-boarding` (multipart, campo `file`) — roda o
  pipeline acima e devolve `BoardingValidationResponse` (status, motivo,
  passageiro/ticket identificados, scores, `is_offline`).
- `GET /health` — liveness simples do processo.
- `GET /local/device/status` — saúde agregada (banco local + vision-service
  + checagem de conectividade ao `central-api` feita na hora) e contagem de
  validações pendentes de sync.
- `GET /local/sync/status` — versão mais barata do anterior: usa o último
  resultado de conectividade já cacheado (não faz novo ping), pensada para
  polling frequente da UI do operador.

## Conectividade (`app/core/connectivity.py`)

`ConnectivityTracker` faz um `GET /health` no `central-api` com timeout
curto (`CENTRAL_API_PING_TIMEOUT_SECONDS`, padrão 2s) e cacheia o
resultado em memória. Decisão deliberada: a validação de embarque
(RNF01, ≤2s por tentativa) nunca espera por esse ping — só
`/local/device/status` o aciona ativamente; `/local/sync/status` e o
pipeline de validação apenas leem o último estado conhecido. Antes da
primeira checagem, assume-se offline por padrão (conservador).

## Sem autenticação — decisão de escopo do MVP

Diferente da `central-api`, o `edge-api` não exige Bearer token: assume-se
rede local confiável a bordo do ônibus (RFC define essa fronteira de
confiança). Não há usuários/admins no edge — o dispositivo embarcado é o
único cliente esperado.

## Testes

```bash
cd apps/edge-api
pytest
```

21 testes: `test_matching.py` (distância de cosseno pura), `test_connectivity.py`
(mocka `httpx.AsyncClient.get`, sem rede real), `test_validation_service.py`
(cobre as 7 ramificações de decisão do pipeline), `test_router.py`
(endpoints via `TestClient`, serviço sobrescrito por dependency override)
e `test_cache_repository.py` (upsert/`list_active` de `EmbeddingCacheRepository`,
incluindo o caso de revogação — `active=False`). `LocalFaceEmbedding`
(coluna `ARRAY(Float)`) é excluída do schema de teste em SQLite — não
suportado nesse dialeto — e testada via mocks na camada de serviço e de
repositório.

## Pendências

- Sem teste de integração ponta a ponta contra um `vision-service` real
  rodando localmente — recomendo validar manualmente após o primeiro boot
  do `buffalo_l`.
- Sem testes de carga/latência (RNF01 exige ≤2s por tentativa).

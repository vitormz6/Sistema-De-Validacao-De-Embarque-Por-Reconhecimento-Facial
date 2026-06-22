# Sync Worker

Worker em background, um por ônibus, que resolve "internet ruim"
(README2 4.5): sincroniza o cache local do `edge-api` com a `central-api`
sem nenhuma API HTTP própria — só um loop assíncrono (RF10, RF11).

## Stack

- **SQLAlchemy (async) + asyncpg** — mesmo `postgres-edge` que o
  `edge-api` usa. Este worker não tem migrations próprias: as tabelas já
  existem, criadas pelas migrations do `edge-api`.
- **httpx** — cliente para `central-api`'s `/sync/pull|push|ack`.
- **Nenhum framework web.** `app/main.py` é só um `while True` com
  `asyncio.sleep`.

## Por que não é uma API

O README2 desenha `sync-worker/app/{outbox,inbox,conflict_resolution,
retry_policy}` como um processo, não um serviço HTTP — e o
`docker-compose.yml` já refletia isso (sem `ports:`). Implementado assim:
um loop de intervalo fixo (`SYNC_INTERVAL_SECONDS`) que cada ciclo tenta
um pull e um push, independentemente.

## Ciclo de sincronização (`app/runner.py`)

```
PULL
  cursor = último cursor salvo (local_sync_state)
  POST /sync/pull {device_id, since: cursor}
    -> upsert local_passengers / local_face_embeddings / local_tickets
    -> salva o novo cursor em local_sync_state
    -> POST /sync/ack {device_id, cursor}

PUSH
  pendentes = local_validation_logs WHERE synced_at IS NULL
  POST /sync/push {device_id, events: [...]}
    -> accepted/duplicated -> marca synced_at
    -> rejected            -> fica pendente, tenta de novo no próximo ciclo
```

Pull e push commitam separadamente — uma falha no push nunca desfaz um
pull que já deu certo, e vice-versa.

## Por que não existe uma tabela `local_sync_outbox` separada

Mesma decisão do `edge-api`: `local_validation_logs.synced_at IS NULL` já
funciona como fila de saída. Esse worker é o único processo que escreve
`synced_at`; o `edge-api` só lê essas linhas.

## Cursor de sincronização (`local_sync_state`)

Nova tabela (migration `20260621_0005` em `apps/edge-api/migrations/`,
já que o `edge-api` é quem possui o schema do `postgres-edge`): uma linha
por `device_id` guardando o `cursor` que `central-api` devolveu no
último `/sync/pull` bem-sucedido. Evita reenviar o histórico completo de
passageiros/embeddings/tickets a cada ciclo.

## Propagação de bloqueio/revogação (não só de novidade)

Esse cursor incremental só funciona de verdade se a `central-api` também
mandar registros que **deixaram** de estar ativos — não só novidades. Um
passageiro bloqueado ou uma passagem cancelada precisam continuar
aparecendo no pull (ver `central-api.md`, seção "Propagação de status no
pull incremental"); este worker não faz nenhum filtro próprio, só upserta
o que `EmbeddingPullItem`/`PassengerPullItem`/`TicketPullItem` trouxerem,
status incluso.

Pra embeddings biométricos especificamente, `EmbeddingPullItem` carrega um
campo `active: bool` (antes não existia) que este worker grava em
`LocalFaceEmbedding.active` via `EmbeddingCacheRepository.upsert`. É o
`edge-api` quem efetivamente filtra por essa coluna ao montar a lista de
candidatos pro matching (`EmbeddingCacheRepository.list_active` lá, não
aqui) — este worker só garante que o valor certo chega ao banco local,
inclusive quando `active=False` (embedding revogado).

## Autenticação

Mesmo esquema do `edge-api` quando ele futuramente chamar a central:
header `X-Device-Key` com o segredo `EDGE_SYNC_API_KEY`, que precisa ser
**idêntico** ao configurado na `central-api` (`verify_edge_device_key`).
Sem isso, todo `/sync/*` responde 401.

## Resolução de conflito

Política deliberadamente simples pro MVP: **central sempre vence** no
pull (upsert sobrescreve o que estiver local). Não há edição local desses
dados — o `edge-api` só lê passageiros/embeddings/tickets, nunca escreve
— então não existe conflito de fato a resolver, só propagação. Do lado do
push, idempotência já é garantida pela `central-api` via `external_id`
(o próprio `id` do log local), então um evento reenviado por retry não
duplica.

## Retry

Sem fila/backoff exponencial: cada ciclo que falhar (central-api fora do
ar, erro de rede) só loga (`sync_cycle_failed`) e tenta de novo no próximo
tick, `SYNC_INTERVAL_SECONDS` depois. Nada se perde nesse intervalo — o
cursor e o outbox local só avançam quando um ciclo completa com sucesso.

## Testes

```bash
cd apps/sync-worker
pytest
```

21 testes: repositórios de cache/sync-state/validação contra SQLite
em memória (exceto `EmbeddingCacheRepository`, mockado — `ARRAY(Float)`
não tem equivalente em SQLite, mesma exclusão do `edge-api`), cliente
HTTP da central mockado (`httpx.AsyncClient.post`) cobrindo sucesso e
`SyncUpstreamError`, e o `SyncRunner` ponta a ponta (pull + push) com o
cliente da central mockado e o banco local real (SQLite). Inclui o caso
de regressão do campo `active` em embeddings revogados (no runner e no
repositório de cache).

## Pendências

- Sem teste de integração real contra `central-api` + Postgres rodando.
- `conflict_resolution`/`retry_policy` como diretórios dedicados (como o
  README2 desenha) não foram criados como módulos separados — a lógica
  é simples o bastante pra caber dentro de `runner.py` sem
  over-engineering; revisar se a complexidade aumentar (ex: backoff
  exponencial, fila de prioridade).
- Sem métricas/observability dedicada (RFC seção 15) além dos logs
  estruturados por ciclo.

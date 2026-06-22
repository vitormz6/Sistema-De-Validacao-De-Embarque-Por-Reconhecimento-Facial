# Central API

API central do sistema de validação de embarque por reconhecimento facial.
Implementa os módulos administrativos (RF01–RF14) descritos no RFC, com
arquitetura em camadas: `router` (HTTP) → `service` (regras de negócio) →
`repository` (acesso a dados) → `model` (SQLAlchemy).

## Módulos

- **passengers** — cadastro de passageiros (RF01).
- **auth** — login (JWT) e gestão de usuários administrativos (RNF03).
- **biometrics** — cadastro biométrico, versionamento de embeddings e
  comparação facial via `vision-service` (RF02, RF03).
- **tickets** — passagens simples vinculadas a um passageiro (RF05).
- **validations** — consulta das tentativas de embarque sincronizadas do
  edge (RF12) e `GET /validations/stats` (contagem por status, RF13 —
  dashboard do `admin-web`).
- **sync** — endpoints `pull`/`push`/`ack`/`status` consumidos pelo
  `sync-worker` no ônibus (RF06, RF10, RF11), mais `GET /sync/devices`
  (lista de dispositivos com `last_pull_at`/`last_push_at`, RF13). Esse
  último vive num `APIRouter` separado (`admin_router`, mesmo prefixo
  `/sync`) porque exige JWT de usuário, não o `X-Device-Key` que protege
  todo o resto do módulo — uma rota não pode "optar por sair" de uma
  dependency declarada no `APIRouter` do qual faz parte.

## Autenticação

- **Usuários administrativos**: `POST /auth/login` retorna um JWT
  (`Bearer`), usado em todos os endpoints de `passengers`, `biometrics`,
  `tickets` e `validations`.
- **Dispositivos edge**: endpoints `/sync/*` são protegidos por um shared
  secret enviado no header `X-Device-Key` (ver `EDGE_SYNC_API_KEY`). Não há
  JWT de usuário para o ônibus — é uma credencial de dispositivo, não de
  pessoa.
- Não existe endpoint público de cadastro de usuário (`POST /auth/users`
  exige um admin autenticado). Para o primeiro admin, rode o script de seed
  (abaixo).

## Vision Service

`biometrics` depende do `vision-service` para detecção facial e geração de
embedding via `POST /embeddings/generate`. O contrato está em
`app/modules/biometrics/vision_client.py`. O serviço está implementado e
orquestrado pelo `docker-compose.yml` (porta 8002) — ver `vision-service.md`.

Os testes de biometria usam um cliente mockado (SQLite em memória não suporta
pgvector), então a integração real deve ser validada manualmente com
`docker compose up` antes da entrega — ver seção de pendências abaixo.

## Propagação de status no pull incremental (`SyncService.pull`)

`PassengerRepository.list_active`, `TicketRepository.list_active` e
`FaceEmbeddingRepository.list_active` recebem um `since` opcional. Regra:

- **Snapshot inicial** (`since=None`): filtra só os registros atualmente
  ativos — não há razão para mandar ao edge um passageiro bloqueado que
  ele nunca viu.
- **Pull incremental** (`since` informado): **não filtra por status**.
  Manda tudo que mudou desde o cursor, esteja ativo ou não.

Esse segundo caso existe por causa de um bug real: a versão anterior
filtrava por status mesmo no incremental (`WHERE status = 'ACTIVE' AND
updated_at > since`). Um passageiro que acabasse de ser bloqueado, ou uma
passagem que acabasse de ser cancelada, deixava de satisfazer a metade
"ativo" do filtro — e como resultado, desaparecia de **todo pull futuro**,
para sempre. O cache do edge nunca aprendia da mudança e continuava
autorizando embarque com base no status antigo.

Pra embeddings biométricos o problema é mais grave: `FaceEmbedding` não
tem `updated_at`, só `created_at` (setado uma vez) e `revoked_at` (setado
uma vez, na revogação). Por isso `FaceEmbeddingRepository.list_active`
incremental usa `created_at > since OR revoked_at > since` em vez de uma
coluna só. Sem o lado `revoked_at`, um embedding revogado (re-enrollment
ou bloqueio do passageiro) nunca mais era enviado — a versão antiga,
já revogada, ficava autorizando embarque offline indefinidamente no
ônibus. `EmbeddingSyncItem` agora carrega um campo `active: bool` para o
edge saber que aquele embedding específico parou de ser válido (em vez de
simplesmente não filtrar nada do lado do edge, como antes — ver
`edge-api.md`).

## Rodando com Docker Compose

Na raiz do projeto:

```bash
docker compose up --build
```

## Migrations

```bash
cd apps/central-api
alembic upgrade head
```

A migration `20260621_0002` habilita a extensão `pgvector` no Postgres —
necessária antes da migration de `face_embeddings`.

## Seed do primeiro administrador

```bash
cd apps/central-api
python -m scripts.seed_admin --email admin@example.com --password "senha-forte" --name "Admin"
```

## Testes

```bash
cd apps/central-api
pytest
```

Os testes usam SQLite em memória (sem dependências externas). A tabela
`face_embeddings` (coluna `vector`, exclusiva do pgvector/Postgres) é
excluída da criação de schema nos testes; o módulo de biometria é testado
com mocks de repositório/`vision_client` em vez de banco real — ver
`tests/conftest.py` e `tests/test_biometrics_service.py`.

## Pendências / próximos passos

- Sem cobertura de testes de integração contra Postgres+pgvector real
  (os testes atuais validam regras de negócio, não o SQL gerado para busca
  vetorial). Recomenda-se rodar `docker compose up postgres-central` e um
  teste manual de `/biometrics/compare` antes da entrega final.
- `/validations/stats` faz uma única query `GROUP BY status` — ok pro
  volume do MVP, mas não tem corte por período (ex: "últimas 24h"); se o
  dashboard precisar disso, é mudança pequena no repositório.

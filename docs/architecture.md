# Arquitetura do Sistema

Sistema de validação de embarque por reconhecimento facial para transporte coletivo. Arquitetura offline-first distribuída em duas camadas: **central** (nuvem) e **edge** (ônibus).

---

## C4 — Nível 1: Contexto

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   [Administrador]          [Operador/Motorista]      [Passageiro]        │
│        │                          │                       │              │
│        │ gerencia cadastros        │ valida embarque        │ embarca     │
│        ▼                          ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐       │
│  │                                                               │       │
│  │         SISTEMA DE VALIDAÇÃO DE EMBARQUE FACIAL               │       │
│  │                                                               │       │
│  │   Plataforma offline-first que autentica passageiros por      │       │
│  │   biometria facial no momento do embarque em ônibus,          │       │
│  │   mesmo sem conexão com a internet.                           │       │
│  │                                                               │       │
│  └───────────────────────────────────────────────────────────────┘       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## C4 — Nível 2: Containers

```
┌─────────────────────────────────── NUVEM ────────────────────────────────┐
│                                                                          │
│  ┌─────────────────┐   REST/JWT   ┌──────────────────────────────────┐  │
│  │   admin-web     │ ───────────▶ │         central-api              │  │
│  │  React + Vite   │              │   FastAPI — router→svc→repo      │  │
│  │  TypeScript     │              │   Módulos: auth, passengers,     │  │
│  │  CSS Modules    │              │   biometrics, tickets,           │  │
│  └─────────────────┘              │   validations, sync              │  │
│                                   └──────────┬──────────┬────────────┘  │
│                                              │          │               │
│                              HTTP/multipart  │          │ SQL+pgvector  │
│                                              ▼          ▼               │
│                              ┌───────────────────┐  ┌──────────────┐   │
│                              │  vision-service   │  │  PostgreSQL  │   │
│                              │  FastAPI          │  │  Central     │   │
│                              │  SCRFD + ArcFace  │  │  + pgvector  │   │
│                              │  ONNX Runtime     │  └──────────────┘   │
│                              └───────────────────┘                     │
│                                                                          │
└───────────────────────────────────▲──────────────────────────────────────┘
                                    │
                          HTTPS — pull/push/ack
                          X-Device-Key auth
                                    │
┌─────────────────────────────── ÔNIBUS ───────────────────────────────────┐
│                                                                          │
│  ┌──────────────────┐  REST   ┌─────────────────────────────────────┐   │
│  │  operator-web    │ ──────▶ │           edge-api                  │   │
│  │  React + Vite    │         │   FastAPI — router→svc→repo         │   │
│  │  TypeScript      │         │   Módulos: validation, health       │   │
│  │  (tela do        │         │   Busca vetorial via NumPy          │   │
│  │   motorista)     │         └──────────────┬──────────────────────┘   │
│  └──────────────────┘                        │                          │
│                                              │ SQL                      │
│  ┌──────────────────┐                        ▼                          │
│  │  sync-worker     │              ┌──────────────────┐                 │
│  │  Python asyncio  │ ──────────▶  │   PostgreSQL     │                 │
│  │  pull → upsert   │              │   Edge (cache)   │                 │
│  │  push → central  │              │   passengers,    │                 │
│  └──────────────────┘              │   embeddings,    │                 │
│                                    │   tickets, logs  │                 │
│                                    └──────────────────┘                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## C4 — Nível 3: Componentes (central-api)

```
central-api/app/
│
├── modules/
│   ├── auth/          router → service → repository
│   │                  JWT login, criação de usuários admin
│   │
│   ├── passengers/    router → service → repository → model
│   │                  CRUD de passageiros
│   │
│   ├── biometrics/    router → service → repository → model
│   │                  Cadastro facial via vision-service
│   │                  Armazena embedding vector(512) + metadados do modelo
│   │
│   ├── tickets/       router → service → repository → model
│   │                  Passagens com validade e vínculo a passageiro
│   │
│   ├── validations/   router → service → repository → model
│   │                  Leitura dos logs de embarque sincronizados do edge
│   │                  GET /validations/stats para dashboard
│   │
│   └── sync/          router (dois APIRouters: device-key + JWT)
│                      service → repository
│                      pull/push/ack consumidos pelo sync-worker
│                      GET /sync/devices para painel admin
│
├── core/              config, security (JWT), exceptions, logging
└── database/          session async, migrations Alembic
```

---

## C4 — Nível 3: Componentes (edge-api)

```
edge-api/app/
│
├── modules/
│   ├── validation/    router → service → repository
│   │                  POST /validate-boarding
│   │                  1. Chama vision-service para gerar embedding
│   │                  2. Busca passageiro mais próximo por distância cosseno
│   │                  3. Verifica passagem ativa
│   │                  4. Persiste log local
│   │                  5. Retorna AUTHORIZED / DENIED_*
│   │
│   ├── cache/         repositories para local_passengers, local_face_embeddings,
│   │                  local_tickets — upsert idempotente via external_id
│   │
│   └── health/        GET /health com status da câmera, banco e sync
│
├── shared/            enums (ValidationStatus, TicketStatus, PassengerStatus)
├── core/              config, connectivity, exceptions, logging
└── database/          session async, migrations Alembic
```

---

## Decisões Técnicas

| Decisão | Escolha | Justificativa |
|---|---|---|
| Embedding facial | ArcFace (InsightFace buffalo_l) | 512-d, SOTA em reconhecimento facial, executa via ONNX |
| Detector facial | SCRFD (InsightFace) | Leve, preciso, roda em edge sem GPU |
| Busca vetorial central | pgvector (PostgreSQL) | Extensão nativa, sem infra adicional |
| Busca vetorial edge | NumPy cosine distance | Sem dependências extras; cache é pequeno |
| Sync | Cursor-based incremental pull + push | Idempotente, tolerante a falha de rede |
| Auth dispositivos edge | X-Device-Key (shared secret) | Sem user session; autenticação de dispositivo |
| Auth admin | JWT Bearer | Stateless, padrão REST |
| ORM | SQLAlchemy async (AsyncSession) | Não bloqueia o event loop do FastAPI |
| Schemas | Pydantic v2 | Validação rápida, integração nativa com FastAPI |
| Frontend | React + TypeScript + Vite + CSS Modules | Sem framework CSS externo, componentes próprios |
| Observabilidade | Prometheus + Grafana | Open-source, integração via prometheus-fastapi-instrumentator |

---

## Fluxo de Sincronização (Pull)

O `sync-worker` roda em loop a cada `SYNC_INTERVAL_SECONDS` segundos:

```
1. Lê cursor (last_pull_at) do banco local
2. POST /sync/pull {device_id, since: cursor}
3. central-api retorna passageiros/embeddings/tickets modificados desde `since`
4. sync-worker faz upsert local (idempotente via external_id = UUID central)
5. Atualiza cursor para result.cursor
6. POST /sync/ack {device_id, cursor}
```

Pull incremental não filtra por status — manda tudo que mudou, inclusive passageiros bloqueados e passagens canceladas, para o edge aprender as mudanças.

---

## Infraestrutura Local (docker-compose)

| Serviço | Porta | Descrição |
|---|---|---|
| postgres-central | 5433 | PostgreSQL + pgvector |
| postgres-edge | 5434 | PostgreSQL edge cache |
| central-api | 8000 | API central (FastAPI) |
| edge-api | 8001 | API edge (FastAPI) |
| vision-service | 8002 | IA: detecção + embedding |
| sync-worker | — | Worker de sync (sem porta HTTP) |
| admin-web | 5173 | Painel admin (React) |
| operator-web | 5174 | Tela do motorista (React) |
| prometheus | 9090 | Coleta de métricas |
| grafana | 3000 | Dashboard de observabilidade |

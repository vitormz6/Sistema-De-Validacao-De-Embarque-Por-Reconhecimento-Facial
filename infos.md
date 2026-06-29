# Guia de Deploy e Infraestrutura

## Ambientes

| Ambiente | Plataforma | Observações |
|---|---|---|
| Produção | Railway | Deploy automático via push no `main` |
| Local | Docker Compose | Para desenvolvimento e testes |

---

## Produção (Railway)

### URLs públicas

| Serviço | URL |
|---|---|
| Admin Web | https://bfv-admin-web.up.railway.app |
| Operator Web | https://operator-web.up.railway.app |
| Central API Docs | https://bfv-central-api.up.railway.app/docs |
| Edge API Docs | https://edge-api-production-8af2.up.railway.app/docs |

### Serviços no Railway

| Serviço Railway | App | Dockerfile |
|---|---|---|
| `central-api` | `apps/central-api` | `infrastructure/docker/central-api.Dockerfile` |
| `edge-api` | `apps/edge-api` | `infrastructure/docker/edge-api.Dockerfile` |
| `vision-service` | `apps/vision-service` | `infrastructure/docker/vision-service.Dockerfile` |
| `sync-worker` | `apps/sync-worker` | `infrastructure/docker/sync-worker.Dockerfile` |
| `admin-web` | `apps/admin-web` | `infrastructure/docker/admin-web.Dockerfile` |
| `operator-web` | `apps/operator-web` | `infrastructure/docker/operator-web.Dockerfile` |
| `Postgres Central` | PostgreSQL 16 + pgvector | Plugin Railway |
| `Postgres Edge` | PostgreSQL 16 | Plugin Railway |

### Variáveis de ambiente obrigatórias

**central-api:**
```
DATABASE_URL=postgresql+asyncpg://...  # Postgres Central (Railway)
VISION_SERVICE_URL=http://vision-service.railway.internal:8002
JWT_SECRET_KEY=<chave secreta longa>
EDGE_SYNC_API_KEY=<segredo compartilhado>
CORS_ORIGINS=["https://bfv-admin-web.up.railway.app"]
ENVIRONMENT=production
DEBUG=false
```

**edge-api:**
```
DATABASE_URL=postgresql+asyncpg://...  # Postgres Edge (Railway)
VISION_SERVICE_URL=http://vision-service.railway.internal:8002
CENTRAL_API_URL=https://bfv-central-api.up.railway.app
EDGE_SYNC_API_KEY=<mesmo segredo do central-api>
CORS_ORIGINS=["https://operator-web.up.railway.app"]
BUS_ID=bus-01
ENVIRONMENT=production
DEBUG=false
```

**sync-worker:**
```
DATABASE_URL=postgresql+asyncpg://...  # Postgres Edge (Railway)
CENTRAL_API_URL=https://bfv-central-api.up.railway.app
EDGE_SYNC_API_KEY=<mesmo segredo do central-api>
BUS_ID=bus-01
SYNC_INTERVAL_SECONDS=30
ENVIRONMENT=production
```

**admin-web:**
```
VITE_API_BASE_URL=https://bfv-central-api.up.railway.app
```

**operator-web:**
```
VITE_EDGE_API_BASE_URL=https://edge-api-production-8af2.up.railway.app
```

### Pós-deploy (primeira vez)

Após subir os serviços pela primeira vez, rode via Console do Railway:

```bash
# No serviço central-api
alembic upgrade head
python -m scripts.seed_admin --email admin@example.com --password "senha" --name "Admin"

# No serviço edge-api
alembic upgrade head
```

---

## Local (Docker Compose)

### Pré-requisitos

- Docker e Docker Compose instalados
- Git

### Subindo os serviços

```bash
git clone https://github.com/vitormz6/Sistema-De-Validacao-De-Embarque-Por-Reconhecimento-Facial.git
cd Sistema-De-Validacao-De-Embarque-Por-Reconhecimento-Facial

docker compose up --build
```

### Primeira inicialização

```bash
# Migrations
docker compose exec central-api alembic upgrade head
docker compose exec edge-api alembic upgrade head

# Seed do administrador
docker compose exec central-api python -m scripts.seed_admin \
  --email admin@example.com --password "senha123" --name "Admin"
```

### URLs locais

| Serviço | URL |
|---|---|
| Admin Web | http://localhost:5173 |
| Operator Web | http://localhost:5174 |
| Central API Docs | http://localhost:8000/docs |
| Edge API Docs | http://localhost:8001/docs |
| Vision Service Docs | http://localhost:8002/docs |

### Observação sobre o vision-service

O `vision-service` baixa os pesos do modelo `buffalo_l` (~500MB) na primeira inicialização — requer conexão com a internet. As execuções seguintes usam o volume Docker `insightface-models` e não precisam baixar novamente.

---

## CI/CD

O pipeline de CI está configurado em `.github/workflows/ci.yml` e executa:

1. Testes de todos os serviços backend (pytest)
2. Testes e build dos frontends (vitest + vite build)
3. Análise estática com SonarCloud

O deploy em produção ocorre automaticamente via integração Railway + GitHub: qualquer push no branch `main` dispara um novo deploy de todos os serviços.

---

## Monitoramento

- **Logs:** disponíveis em tempo real na aba "Logs" de cada serviço no Railway.
- **Métricas:** CPU e memória visíveis na aba "Metrics" do Railway.
- **Health checks:**
  - Central API: `GET /health`
  - Edge API: `GET /health` e `GET /local/device/status`
  - Vision Service: `GET /health` e `GET /health/models`

---

## Configuração do SonarCloud

1. Acesse https://sonarcloud.io e faça login com GitHub.
2. Crie uma organização vinculada ao seu GitHub (`vitormz6`).
3. Importe o repositório.
4. Gere um token em **My Account → Security → Generate Token**.
5. Adicione o token como secret no GitHub: `Settings → Secrets and variables → Actions → SONAR_TOKEN`.
6. O arquivo `sonar-project.properties` na raiz já está configurado.

-   **No ônibus** roda a validação local, câmera, IA, banco local/cache e sincronização.
-   **Na nuvem/servidor central** ficam cadastros, passagens, gestão da frota, auditoria, dashboards, usuários e relatórios.
-   **No admin React** ficam telas para operadores, gestores, empresas e suporte.

A ideia é não depender 100% da internet dentro do ônibus, mas também não deixar cada ônibus isolado.

----------

# 1. Visão macro da arquitetura

# Arquitetura Geral do Sistema

```
┌──────────────────────────────────────────────────────────────┐
│                       CLOUD / DATA CENTER                    │
│                                                              │
│  ┌──────────────────┐    ┌──────────────────────────────┐    │
│  │ Admin Web React  │───▶│ API Central FastAPI          │    │
│  └──────────────────┘    └──────────────┬───────────────┘    │
│                                         │                    │
│                           ┌─────────────▼──────────────┐     │
│                           │ PostgreSQL Central          │    │
│                           │ passageiros, passagens,     │    │
│                           │ empresas, logs, auditoria   │    │
│                           └─────────────┬──────────────┘     │
│                                         │                    │
│                           ┌─────────────▼──────────────┐     │
│                           │ Object Storage              │    │
│                           │ fotos autorizadas, docs,    │    │
│                           │ evidências, backups         │    │
│                           └────────────────────────────┘     │
│                                                              │
└───────────────────────────────▲──────────────────────────────┘
                                │
                                │ sync seguro
                                │
┌───────────────────────────────┴──────────────────────────────┐
│                          ÔNIBUS / EDGE                       │
│                                                              │
│  ┌──────────┐    ┌─-─────────────────┐    ┌──────────────┐   │
│  │ Câmera   │───▶│ Vision Service    │──▶│ Local API    │   │
│  └──────────┘    │ SCRFD + ArcFace   │    │ FastAPI      │   │
│                  └────────┬────────-─┘    └──────┬───────┘   │
│                           │                     │            │
│                  ┌────────▼─────────┐   ┌──────▼────────┐    │
│                  │ Local PostgreSQL │   │ Sync Worker   │    │
│                  │                  │   │ Outbox/Inbox  │    │
│                  └──────────────────┘   └───────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Tela Local do Motorista/Operador                       │  │
│  │ Autorizado / Negado / Offline                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

----------

# 2. Separação principal: Edge e Central

## 2.1. Edge: o que roda no ônibus

Essa é a parte que precisa funcionar mesmo sem internet.

### Componentes do ônibus
| Componente | Responsabilidade |
|--|--|
| Camera Capture Service | Captura frames da câmera |
| Vision Service | Detecta face, gera embedding, liveness básico
|Validation Service|Decide se passageiro pode embarcar
|Local API|Expõe endpoints locais para a tela do ônibus
|Local Database|Guarda cache de passageiros, passagens e logs
|Sync Worker|Sincroniza dados com servidor central
|Operator UI | Tela simples para motorista/validador

----------

## 2.2. Central: o que roda no servidor

Essa é a parte administrativa e gerencial.

### Componentes centrais

| Componente |Responsabilidade  |
|--|--|
|Admin Web React|Painel administrativo
|Central API|API principal do sistema
|Auth Service|Login, permissões e papéis
|Passenger Service|Cadastro de passageiros
|Ticket Service| Passagens, validade
|Fleet Service|ônibus, linhas
|Biometric Service|Cadastro facial, embeddings
|Sync Service|Recebe/envia dados dos ônibus
|Audit Service|Logs, rastreabilidade, LGPD

----------

# 3. Stack

## 3.1. Backend

**FastAPI** para a API principal e para o edge.

| Parte | Tecnologia |
|--|--|
|API central|FastAPI
|API local do ônibus|FastAPI
|Validação de dados|Pydantic
|ORM|SQLAlchemy
|Migrações|Alembic
|Cache|Redis



----------

## 3.2. IA / Visão Computacional

|Função| Tecnologia |
|--|--|
|Captura|OpenCV
|Detecção facial|SCRFD
|Reconhecimento facial|ArcFace/InsightFace
|Inferência otimizada|ONNX Runtime
|Busca vetorial|pgvector
|Liveness básico|módulo próprio inicialmente
|Deploy IA edge|ONNX Runtime / Docker

O ONNX Runtime é apropriado porque permite rodar modelos de machine learning em diferentes hardwares e sistemas operacionais, incluindo cenários IoT/edge.

----------

## 3.3. Banco

**PostgreSQL + pgvector** no central. Para o edge, existem duas opções:

|Cenário| Banco |
|--|--|
|Produto real robusto|PostgreSQL local
|Frota grande|PostgreSQL local + sync incremental

Minha escolha para produto real:

```
Central: PostgreSQL + pgvectorEdge: PostgreSQL
```

----------

## 3.4. Frontend

|Interface| Tecnologia |
|--|--|
|Admin web|React + TypeScript
|Design System|Ant Design
|Estado remoto|TanStack Query
|Formulários|React Hook Form + Zod
|Build|Vite
|Testes|Vitest + Testing Library
|E2E|Playwright

----------

# 4. Aplicações do sistema

Eu dividiria em **5 aplicações principais**.

----------

## 4.1. `admin-web`

Painel React usado por administradores, operadores, gestores e suporte.

```
admin-web/
├── src/
│   ├── app/
│   ├── pages/
│   ├── modules/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── passengers/
│   │   ├── enrollments/
│   │   ├── tickets/
│   │   ├── fleet/
│   │   ├── devices/
│   │   ├── validations/
│   │   ├── reports/
│   │   └── audit/
│   ├── components/
│   ├── services/
│   ├── hooks/
│   ├── schemas/
│   └── routes/
```

----------

## 4.2. `central-api`

API principal do sistema.

```
central-api/  
├── app/  
│ ├── main.py  
│ ├── core/  
│ │ ├── config.py  
│ │ └── logging.py  
│ ├── modules/  
│ │ ├── passengers/  
│ │ ├── biometrics/  
│ │ ├── tickets/  
│ │ ├── fleet/  
│ │ ├── validations/  
│ │ ├── sync/  
│ │ └── audit/  
│ ├── database/  
│ └── shared/  
├── migrations/  
└── tests/
```

----------

## 4.3. `edge-api`

API local do ônibus.

```
edge-api/  
├── app/  
│ ├── main.py  
│ ├── modules/  
│ │ ├── camera/  
│ │ ├── validation/  
│ │ ├── sync/  
│ │ └── health/  
│ ├── database/  
│ └── shared/
```


-   validar embarque;
-   consultar status;
-   receber atualização de passageiros/passagens;
-   registrar logs;
-   sincronizar.

----------

## 4.4. `vision-service`

Serviço isolado para IA.

```
vision-service/
├── app/
│   ├── main.py
│   ├── camera/
│   │   ├── capture.py
│   │   └── frame_buffer.py
│   ├── detection/
│   │   └── scrfd_detector.py
│   ├── recognition/
│   │   └── arcface_embedder.py
│   ├── liveness/
│   │   └── liveness.py
│   ├── quality/
│   │   └── face_quality.py
│   └── schemas/
├── models/
│   ├── scrfd.onnx
│   └── arcface.onnx
└── tests/
```

Aqui fica tudo que é “IA”. Isso evita misturar visão computacional com regra de negócio.

----------

## 4.5. `sync-worker`

Worker de sincronização entre ônibus e central.

```
sync-worker/
├── app/
│   ├── main.py
│   ├── outbox/
│   ├── inbox/
│   ├── conflict_resolution/
│   └── retry_policy/
```

Esse cara resolve o maior problema real: internet ruim.

----------

# 5. Módulos do backend central

## 5.3. Passageiros

Responsável por:

-   cadastro pessoal;
-   documento;
-   foto;
-   status;
-   biometria;
-   vínculo com cartões/passagens;
-   histórico de validações.

----------

## 5.4. Biometria

Responsável por:

-   cadastro facial;
-   geração de embedding;
-   armazenamento do vetor;
-   versionamento do modelo;
-   revogação de biometria;
-   recadastramento;
-   score mínimo;
-   qualidade da imagem;

Ponto importante: **o modelo precisa ter versão**.

Exemplo:

```
embedding gerado com:
model_name = arcface
model_version = buffalo_l_v1
detector = scrfd
created_at = 2026-06-02
```

Por quê? Porque se um dia você trocar o modelo, os embeddings antigos podem não ser compatíveis.

----------

## 5.5. Passagens

Responsável por:

-   passagem ativa;
-   validade;
-   linha;
-   validade por horário/rota.
----------

## 5.8. Validações

Cada tentativa de embarque gera um evento:

```
validacao_id
passageiro_identificado_id
onibus_id
linha_id
score
status
motivo
timestamp
offline
synced_at
```

Status possíveis:

```
AUTHORIZED
DENIED_NO_ACTIVE_TICKET
DENIED_LOW_CONFIDENCE
DENIED_FACE_NOT_FOUND
DENIED_SPOOF_SUSPECTED
DENIED_PASSENGER_BLOCKED
```

----------

## 5.9. Auditoria

Tudo que envolve dado sensível precisa deixar rastro:

```
quem acessou
quando acessou
qual dado acessou
qual ação executou
IP/origem
antes/depois quando aplicável
```

----------

# 6. Banco de dados central

Modelo inicial de tabelas:

```
users

passengers
passenger_documents
passenger_photos
face_embeddings
biometric_enrollments

tickets
ticket_usages

routes
route_stops

boarding_validations
validation_events
validation_evidences

sync_batches
sync_outbox
sync_inbox
sync_conflicts

audit_logs
```

----------

## 6.1. Tabelas principais

### `passengers`

```
id
full_name
birth_date
status
created_at
updated_at
```
----------

### `face_embeddings`

```
id
passenger_id
embedding vector(512)
model_name
model_version
detector_name
detector_version
quality_score
active
created_at
revoked_at
```

Aqui entra o pgvector.

----------

### `tickets`

```
id
passenger_id
status
valid_from
valid_until
route_id
created_at
updated_at
```

----------

### `boarding_validations`

```
id
bus_id
route_id
passenger_id
ticket_id
status
confidence_score
similarity_distance
reason_code
is_offline
captured_at
synced_at
created_at
```

----------

### `sync_outbox`

```
id
aggregate_type
aggregate_id
event_type
payload
status
attempts
created_at
sent_at
error_message
```

Essa tabela é essencial para o offline-first.

----------

# 7. Banco local do ônibus

O banco local não precisa ter tudo. Ele precisa ter apenas o necessário para operar.

```
local_passengers
local_face_embeddings
local_tickets
local_validation_logs
local_sync_outbox
local_sync_inbox
```

## Dados que vão para o ônibus

```
passageiros ativos linha
embeddings ativos
passagens válidas
regras de validação
configurações do dispositivo
versão dos modelos
```

## Dados que voltam do ônibus

```
logs de validação
eventos de falha
eventos de saúde
tentativas negadas
uso de passagem
evidências minimizadas
```

----------

# 8. Fluxo de cadastro facial

```
Admin Web
  ↓
Tela de cadastro do passageiro
  ↓
Captura ou upload de foto
  ↓
API Central
  ↓
Vision Service
  ↓
SCRFD detecta face
  ↓
Face quality check
  ↓
ArcFace gera embedding
  ↓
Salva embedding no PostgreSQL + pgvector
  ↓
Marca passageiro como biometria ativa
  ↓
Sync envia para ônibus aplicáveis
```

----------

# 9. Fluxo de validação no ônibus

```
Câmera captura frame
  ↓
Vision Service detecta face com SCRFD
  ↓
Verifica qualidade mínima
  ↓
Executa liveness
  ↓
Gera embedding com ArcFace
  ↓
Busca passageiro similar no banco local
  ↓
Valida threshold
  ↓
Consulta passagem ativa local
  ↓
Autoriza ou nega
  ↓
Mostra resultado na tela local
  ↓
Registra log local
  ↓
Sync envia evento ao central quando houver conexão
```

----------

# 10. Telas do Admin React

Agora a parte que você pediu: **telas de admin, cadastro, operação, tudo.**

----------

## 10.2. Dashboard geral

```
/dashboard
```

Cards:

-   embarques hoje;
-   autorizados;
-   negados;
-   taxa de baixa confiança;
-   ônibus online;
-   ônibus offline;
-   dispositivos com falha;
-   sincronizações pendentes;
-   passageiros ativos;
-   passagens ativas.

Gráficos:

-   validações por hora;
-   negações por motivo;
-   top linhas com maior fluxo;
-   dispositivos com mais erro;
-   comparação online/offline.

----------

## 10.3. Passageiros

```
/passengers
/passengers/new
/passengers/:id
/passengers/:id/edit
```

Funcionalidades:

-   listar passageiros;
-   filtrar por status;
-   buscar por nome;
-   cadastrar passageiro;
-   editar dados;
-   bloquear passageiro;
-   consultar histórico;
-   revogar biometria;
-   reenviar para sincronização.

Campos:

```
nome
documento
data de nascimento
telefone
e-mail
status
observações / se precisar sei lá
```

----------

## 10.4. Cadastro biométrico

```
/passengers/:id/biometrics
/passengers/:id/biometrics/enroll
```

Tela muito importante.

Funcionalidades:

-   capturar foto pela webcam;
-   upload de imagem;
-   validar qualidade;
-   detectar face;
-   mostrar score de qualidade;
-   gerar embedding;
-   confirmar cadastro;
-   exibir modelo usado;
-   revogar biometria;
-   recadastrar.

Status:

```
Sem biometria
Biometria ativa
Biometria revogada
Cadastro pendente
Imagem inválida
Baixa qualidade
```

----------

## 10.6. Passagens

```
/tickets
/tickets/new
/tickets/:id
```

Funcionalidades:

-   criar passagem;
-   associar passageiro;
-   definir validade;
-   associar linha/rota;
-   bloquear passagem;
-   consultar uso;
-   importar lote de passagens.

Tipos:

```
unitáriamensalestudantecolaboradorvale-transporteespecial
```

----------

## 10.7. Linhas e rotas

```
/routes
/routes/new
/routes/:id
```

Funcionalidades:

-   cadastrar linha;
-   cadastrar pontos;
-   associar ônibus;
-   associar dispositivos;

----------

## 10.10. Validações de embarque

```
/validations
/validations/:id
```

Filtros:

-   data;
-   passageiro;
-   linha;
-   status;
-   score;
-   motivo de negação;
-   validações offline.

Colunas:

```
data/hora
passageiro
linha
status
score
motivo
offline/sincronizado
```

Detalhe da validação:

```
passageiro identificado
score
passagem usada
modelo de IA
distância vetorial
motivo
log técnico
```

----------

## 10.11. Auditoria

```
/audit
```

Funcionalidades:

-   quem acessou dado biométrico;
-   quem cadastrou passageiro;
-   quem revogou consentimento;
-   quem alterou passagem;
-   quem vinculou dispositivo;
-   exportação CSV;
-   filtros por usuário, ação e período.

----------

## 10.12. Relatórios

```
/reports
```

Relatórios:

-   embarques por período;
-   uso por linha;
-   passageiros ativos;
-   taxa de negação;
-   taxa de baixa confiança;
-   dispositivos com falha;
-   passagens utilizadas;
-   passageiros mais recorrentes;
-   operação offline por veículo.

----------

## 10.13. Configurações

```
/settings
```

Configurações:

-   threshold mínimo de reconhecimento;
-   distância máxima;
-   política de baixa confiança;
-   tempo de cooldown entre embarques;
-   retenção de logs;
-   retenção de imagens;
-   versão ativa dos modelos;
-   regras de sincronização;
-   usuários;

----------

# 11. Tela local do ônibus

Essa tela precisa ser simples, rápida e segura.

```
/operator
```

Estados principais:

## Aguardando passageiro

```
Aguardando rosto...
Status: Online/Offline
Câmera: OK
Última sincronização: 10:32
```

## Autorizado

```
EMBARQUE AUTORIZADO

Passageiro: João S.
Linha: 101
Passagem: Ativa
Confiança: 91%
```

## Negado

```
EMBARQUE NEGADO

Motivo: passagem expirada
```

## Baixa confiança

```
VALIDAÇÃO NÃO CONCLUÍDA

Motivo: baixa confiança facial
Ação: validar manualmente ou usar QR Code/cartão
```

## Sem internet

```
MODO OFFLINE

Validações locais ativas
Eventos serão sincronizados depois
```

----------

# 12. APIs principais


## Passageiros

```
GET    /passengers
POST   /passengers
GET    /passengers/{id}
PUT    /passengers/{id}
DELETE /passengers/{id}
POST   /passengers/{id}/block
POST   /passengers/{id}/unblock
```

## Biometria

```
POST /passengers/{id}/biometrics/enroll
GET  /passengers/{id}/biometrics
POST /passengers/{id}/biometrics/revoke
POST /biometrics/compare
```

## Passagens

```
GET  /tickets
POST /tickets
GET  /tickets/{id}
PUT  /tickets/{id}
POST /tickets/{id}/block
POST /tickets/{id}/activate
```

## Validações

```
GET  /validations
GET  /validations/{id}
```

## Sync

```
POST /sync/pull
POST /sync/push
POST /sync/ack
GET  /sync/status
```

## Edge local

```
POST /local/validate-boarding
GET  /local/device/status
GET  /local/sync/status
POST /local/sync/run
```

----------

# 13. Comunicação entre edge e central

Com **outbox pattern**.

## No ônibus

Quando algo acontece:

```
validação criada
passagem usada
erro de câmera
erro de IA
```

Salva primeiro localmente:

```
local_sync_outbox
```

Depois o sync-worker tenta enviar.

Se falhar:

```
incrementa attempts
mantém status PENDING
tenta depois
```

----------

## No central

O central envia:

```
novos passageiros
embeddings atualizados
passagens atualizadas
bloqueios
novas configurações
nova versão de modelo
```

O ônibus aplica localmente.

----------

# 14. Segurança


## 14.2. Dados sensíveis

Biometria precisa ser tratada como dado sensível.

```
criptografia em repouso
criptografia em trânsito
auditoria de acesso
retenção limitada
minimização de imagens
armazenar embedding, não imagem crua sempre
```

----------

## 14.3. Imagens

Evitaria salvar imagem de toda validação.

|Caso| Salvar Imagem? |
|--|--|
|Autorizado normal|Não
|Negado por baixa confiança|Opcional, com retenção curta
|Suspeita de fraude|Opcional, com regra clara
|Auditoria/LGPD|Somente se necessário

----------

# 15. Observabilidade

Produto real precisa disso.

## Métricas

```
tempo médio de validação
tempo da busca vetorial
taxa de autorização
taxa de negação
taxa de baixa confiança
sync pendente
```

## Logs

Formato JSON:

```
{  
"event": "boarding_validation",   
"status": "AUTHORIZED",  
"confidence": 0.91,  
"latency_ms": 348,  
"offline": true  
}
```

## Health checks

```
GET /health
GET /health/database
GET /health/camera
GET /health/models
GET /health/sync
```

----------

# 16. Deploy

## Ambiente local/dev

```
Docker Compose
```

Serviços:

```
admin-web
central-api
postgres
redis
vision-service
sync-worker
```

----------

## Produção central

```
PostgreSQL gerenciado
Redis gerenciado
Object Storage
API Gateway
Load Balancer
Observabilidade
```

----------

## Produção edge/ônibus

```
Mini-PC industrial ou Jetson
Docker Compose
watchdog
banco local
modelos ONNX locais
sync-worker local
logs rotacionados
```

----------

# 17. Estrutura de monorepo

Eu faria assim:

```
boarding-face-validation/
├── apps/
│   ├── admin-web/
│   ├── operator-web/
│   ├── central-api/
│   ├── edge-api/
│   ├── vision-service/
│   └── sync-worker/
│
├── infrastructure/
│   ├── docker/
│   ├── nginx/
│   └── monitoring/
│
└── README.md -> e um readme.md em cada "app"
```

----------

# 18. Arquitetura no TCC

O nome técnico poderia ser:

> **Plataforma offline-first de validação de embarque por biometria facial em transporte coletivo, baseada em inferência edge, busca vetorial e sincronização distribuída.**

E a tese técnica seria:

> O sistema propõe uma arquitetura distribuída em que a validação de embarque ocorre localmente no veículo, reduzindo dependência de conectividade, enquanto a gestão, auditoria, sincronização e análise operacional são centralizadas em uma plataforma administrativa web.

----------

# 19. Resumo final da arquitetura ideal

```
Frontend Admin:
React + TypeScript + Vite

Tela local:
React simples

Backend central:
FastAPI + Alembic + Workers

Backend edge:
FastAPI local + banco local + sync worker

IA:
SCRFD para detecção facial
ArcFace/InsightFace para embeddings
ONNX Runtime para inferência edge
Liveness qualidade top
Face quality check

Banco:
PostgreSQL + pgvector central
PostgreSQL local no ônibus

Infra:
Docker Compose no edge
Docker
Object Storage
Observabilidade

Segurança:
Criptografia
Auditoria
Retenção controlada

Admin:
passageiros
biometria
passagens
frota
linhas
validações
relatórios
auditoria
configurações
```

Minha recomendação: **não faça como um app único**. Faça como uma plataforma modular com **central + edge + IA isolada + admin web**. Isso transforma seu TCC de “sistema que reconhece rosto” em um projeto de arquitetura de software real, vendável e defensável.
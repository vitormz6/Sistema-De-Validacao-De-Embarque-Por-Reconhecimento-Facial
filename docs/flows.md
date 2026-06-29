# Fluxos de Negócio

Os três fluxos principais do sistema.

---

## Fluxo 1 — Cadastro de Passageiro e Biometria

```
Administrador (admin-web)
    │
    ├─ 1. Preenche dados do passageiro (nome, documento)
    │      POST /passengers
    │      → passenger.id criado, status=ACTIVE
    │
    ├─ 2. Abre tela de biometria do passageiro
    │      Captura foto via webcam ou upload de imagem
    │
    ├─ 3. Envia imagem para cadastro facial
    │      POST /passengers/{id}/biometrics/enroll
    │      │
    │      ▼ central-api
    │      Repassa imagem para vision-service
    │      POST vision-service /embeddings/generate
    │      │
    │      ▼ vision-service
    │      SCRFD detecta face na imagem
    │      Verifica qualidade mínima (quality_score ≥ threshold)
    │      Verifica liveness (liveness_score ≥ threshold)
    │      ArcFace gera embedding vector(512)
    │      Retorna {embedding, quality_score, liveness_score, model_name, model_version}
    │      │
    │      ▼ central-api
    │      Salva face_embeddings com embedding + metadados
    │      Marca passenger como tendo biometria ativa
    │
    └─ 4. Resposta visual de sucesso / falha na tela admin
           (falha: face não encontrada, baixa qualidade, suspeita de spoof)
```

---

## Fluxo 2 — Sincronização Central → Edge

```
sync-worker (rodando no ônibus a cada N segundos)
    │
    ├─ Pull cycle
    │   │
    │   ├─ 1. Lê last_pull_cursor do banco local (null na primeira execução)
    │   │
    │   ├─ 2. POST central-api /sync/pull
    │   │      { device_id: "bus-01", since: cursor }
    │   │
    │   │      central-api responde com:
    │   │      {
    │   │        passengers: [...],   ← todos os modificados desde `since`
    │   │        embeddings: [...],   ← incluindo active=false (revogados)
    │   │        tickets: [...],      ← incluindo cancelados
    │   │        cursor: "2026-06-28T..."
    │   │      }
    │   │
    │   ├─ 3. Faz upsert local de cada item (idempotente via UUID do central)
    │   │
    │   ├─ 4. Atualiza cursor local
    │   │
    │   └─ 5. POST central-api /sync/ack { cursor }
    │
    └─ Push cycle
        │
        ├─ 1. Busca local_validation_logs com synced_to_central=false
        │
        ├─ 2. POST central-api /sync/push
        │      { device_id, events: [...] }
        │
        ├─ 3. central-api persiste os logs em boarding_validations
        │      (dedup via external_id — idempotente)
        │
        └─ 4. sync-worker marca os logs enviados como synced_to_central=true
```

---

## Fluxo 3 — Validação de Embarque no Ônibus

```
Passageiro se aproxima da câmera
    │
    ▼
operator-web (tela do motorista)
    │
    ├─ 1. Captura frame da câmera via WebRTC
    │
    ├─ 2. POST edge-api /validate-boarding (multipart: imagem)
    │
    │      ▼ edge-api
    │      Repassa imagem para vision-service
    │      POST vision-service /embeddings/generate
    │      │
    │      ▼ vision-service
    │      SCRFD detecta face
    │      Se não detectar: retorna erro → edge responde DENIED_FACE_NOT_FOUND
    │      Verifica quality_score ≥ threshold
    │      Verifica liveness_score ≥ threshold
    │      Se liveness falhar: edge responde DENIED_SPOOF_SUSPECTED
    │      ArcFace gera embedding 512-d
    │      │
    │      ▼ edge-api
    │      Busca local_face_embeddings com active=true
    │      Calcula distância cosseno entre embedding gerado e todos os embeddings do cache
    │      Encontra o mais próximo (menor distância)
    │
    │      Se distância > threshold_max → DENIED_LOW_CONFIDENCE
    │      │
    │      Busca local_tickets do passenger_id encontrado
    │      Se nenhuma passagem ativa no momento → DENIED_NO_ACTIVE_TICKET
    │      Se passageiro bloqueado → DENIED_PASSENGER_BLOCKED
    │      │
    │      → AUTHORIZED
    │
    ├─ 3. Persiste log em local_validation_logs (synced_to_central=false)
    │
    └─ 4. Retorna resultado para operator-web
           Tela exibe: AUTORIZADO (verde) / NEGADO (vermelho) + motivo
```

---

## Fluxo Alternativo — Operação Offline

Quando o ônibus não tem conexão com a internet:

```
sync-worker tenta pull/push → falha (timeout / connection refused)
    │
    └─ Registra falha nos logs, incrementa retry counter
       Continua tentando no próximo ciclo (intervalo configurável)

edge-api continua operando normalmente:
    │
    ├─ Usa o snapshot mais recente do banco local (última sincronização bem-sucedida)
    ├─ Todas as validações são registradas com is_offline=true
    └─ Quando a conexão voltar, sync-worker envia todos os logs pendentes
       (dedup no central via external_id garante idempotência)
```

---

## Estados de Validação

| Status | Descrição |
|---|---|
| `AUTHORIZED` | Passageiro identificado com confidence suficiente e passagem ativa |
| `DENIED_FACE_NOT_FOUND` | Nenhuma face detectada na imagem |
| `DENIED_LOW_CONFIDENCE` | Distância cosseno acima do threshold — face detectada mas não identificada com certeza |
| `DENIED_SPOOF_SUSPECTED` | Liveness score abaixo do threshold — possível foto ou vídeo |
| `DENIED_NO_ACTIVE_TICKET` | Passageiro identificado mas sem passagem válida no momento |
| `DENIED_PASSENGER_BLOCKED` | Passageiro identificado mas com status BLOCKED no sistema |

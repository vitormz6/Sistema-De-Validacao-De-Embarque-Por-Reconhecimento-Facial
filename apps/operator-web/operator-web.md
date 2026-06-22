# Operator Web

Tela kiosk do validador de embarque, projetada para rodar em um tablet ou
mini-PC embarcado no ônibus. Exibe o feed da câmera, detecta rostos
automaticamente via `TinyFaceDetector` (client-side) e dispara a validação
sem interação manual, apresentando o resultado (`AUTORIZADO` / `NEGADO`)
com feedback visual e reset automático em 4 s.

## Stack

- **React + TypeScript + Vite** — SPA de tela única, sem roteamento.
- **TanStack Query** — `useMutation` para a chamada de validação;
  `useQuery` com `refetchInterval` para polling do status de sincronização.
- **axios** — cliente HTTP sem `Authorization` header (o `edge-api`
  não autentica chamadas locais por design — ver `edge-api.md`).
- **@vladmandic/face-api** — detecção facial client-side com modelo
  `TinyFaceDetector` (pesos servidos em `public/models/`). Dispara captura
  automática quando `score ≥ 0.6`, com cooldown de 4 s entre capturas.
- **CSS Modules sobre `src/styles/tokens.css`** — mesmos tokens do
  `admin-web`, sem tema escuro (kiosk fixo, sem toggle de tema).
- **Vitest + Testing Library** — setup jsdom mínimo.

## Comportamento

### Máquina de estados da tela

| Estado | O que o operador vê |
|--------|----------------------|
| `idle` | Feed da câmera + overlay de scanning; detecção automática ativa |
| `processing` | Overlay de spinner sobre a câmera; detecção pausada |
| `result` | Card AUTORIZADO/NEGADO substitui a câmera; reset automático em 4 s |

### Fluxo de validação (RF07–RF09)

1. Loop `requestAnimationFrame` detecta rostos via `TinyFaceDetector`
   enquanto o estado é `idle`.
2. Ao detectar um rosto (`score ≥ 0.6`) sem cooldown ativo, um frame
   JPEG é extraído do `<video>` via `<canvas>` oculto.
3. `POST /local/validate-boarding` (multipart/form-data) ao `edge-api` local.
4. Card de resultado exibe:
   - **AUTORIZADO** (verde): nome do passageiro, percentual de confiança.
   - **NEGADO** (vermelho): motivo traduzido para PT-BR (`ValidationStatus`).
5. Respostas `DENIED_FACE_NOT_FOUND` retornam silenciosamente ao estado
   `idle` sem exibir card (face detectada client-side mas não encontrada
   pelo `edge-api` — captura de baixa qualidade ou rosto muito distante).
6. Após 4 s, tela retorna ao estado `idle` automaticamente; cooldown
   também expira, permitindo nova captura.

### Indicador de sincronização (RF14)

`SyncStatusBar` (barra superior) faz polling de `GET /local/sync/status`
a cada 10 s e exibe:

- **●Online / ●Offline** — campo `is_offline` retornado pelo `edge-api`
  (que reflete o último ping ao `central-api` feito pelo `ConnectivityTracker`).
- **N pendentes** — profundidade da fila de `local_validation_logs` não
  sincronizados; permite ao operador perceber se o `sync-worker` está travado.

## Estrutura

```
src/
├── api/
│   ├── httpClient.ts       # axios sem auth (herdado do scaffold)
│   ├── syncApi.ts          # GET /local/sync/status
│   └── validationApi.ts    # POST /local/validate-boarding
├── app/
│   └── queryClient.ts      # QueryClient (herdado do scaffold)
├── modules/
│   └── validation/
│       ├── CameraCapture.tsx          # feed da câmera + captura via canvas
│       ├── CameraCapture.module.css
│       ├── ResultCard.tsx             # card AUTORIZADO/NEGADO + countdown
│       ├── ResultCard.module.css
│       ├── SyncStatusBar.tsx          # barra superior online/offline
│       ├── SyncStatusBar.module.css
│       ├── ValidationPage.tsx         # máquina de estados principal
│       └── ValidationPage.module.css
├── styles/
│   ├── global.css   # reset + overrides de kiosk (herdado do scaffold)
│   └── tokens.css   # design tokens (herdado do scaffold)
├── test/
│   └── setup.ts     # polyfills jsdom: matchMedia + mediaDevices
├── types/
│   └── index.ts     # espelha schemas do edge-api
├── App.tsx           # raiz — apenas renderiza ValidationPage
└── main.tsx          # bootstrap React + QueryClientProvider
```

## Por que não usa React Router

O `operator-web` é uma **tela única de kiosk** — não há login, navegação
entre páginas nem URL compartilhável. Adicionar React Router aumentaria a
complexidade sem benefício funcional.

## Câmera e detecção automática

`CameraCapture` chama `navigator.mediaDevices.getUserMedia` com
`facingMode: "user"` (câmera frontal). Se o navegador negar a permissão,
o componente exibe um aviso e a detecção não inicia — o operador precisa
conceder a permissão manualmente.

O modelo `TinyFaceDetector` é carregado uma vez na montagem do componente a
partir de `public/models/`. Enquanto carrega (câmera + modelo), o status
exibe "Iniciando câmera...". O loop de detecção só começa após ambos
estarem prontos.

Sobre o overlay de detecção: um `<canvas>` sobreposto ao `<video>` desenha
cantos estilizados ao redor do rosto detectado em tempo real. Quando nenhum
rosto é detectado, exibe uma animação de scanning estática com linha
horizontal pulsante.

Para tablet horizontal apontando para a porta de embarque, alterar para
`facingMode: "environment"` (câmera traseira) pode ser parametrizado via
`VITE_CAMERA_FACING_MODE`.

## Rodando

```bash
cd apps/operator-web
npm install
npm run dev    # http://localhost:5174
```

Ou via `docker compose up operator-web` (requer `edge-api` já no ar).

O endereço do `edge-api` é lido de `VITE_EDGE_API_BASE_URL`
(padrão: `http://localhost:8001`). Como o navegador roda na máquina do
operador (não dentro da rede do compose), o valor deve ser um host
acessível pelo tablet — ver `.env.example` para mais detalhes.

## Pendências / próximos passos

- `VITE_CAMERA_FACING_MODE` para configurar câmera frontal/traseira via env.
- `VITE_CAPTURE_COOLDOWN_MS` para tornar o cooldown de 4 s configurável.
- Build de produção com nginx (mesma razão que o `admin-web`).
- Testes de integração contra o `edge-api` real.

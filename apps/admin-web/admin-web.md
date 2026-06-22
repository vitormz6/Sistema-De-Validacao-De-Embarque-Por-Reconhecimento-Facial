# Admin Web

Painel administrativo React. Cobre o recorte de MVP do RFC: cadastro de
passageiro (RF01), cadastro biométrico por upload/captura (RF02),
cadastro simples de passagem (RF05), consulta de validações (RF12) e
dashboard operacional básico (RF13).

## Stack

- **React + TypeScript + Vite** — SPA, sem SSR.
- **UI própria, sem biblioteca de componentes** (`src/components/ui/`)
  — ver seção dedicada abaixo.
- **TanStack Query** — cache/estado de dados remotos (toda chamada à
  `central-api` passa por aqui, nunca por `useState`+`useEffect` solto).
- **React Hook Form + Zod** — formulários e validação client-side,
  espelhando as mesmas regras dos schemas Pydantic da `central-api`
  (ver `*Schema.ts` em cada módulo).
- **React Router** — rotas client-side.
- **dayjs** — formatação/parsing de datas (única dependência "de UI"
  que sobrou de fora, por ser utilitário puro, não componente visual).
- **Vitest + Testing Library** — testes unitários/integração de
  componentes. Sem Playwright/E2E — fora do escopo de tempo do TCC.

## UI própria (`src/components/ui/`)

Sem AntD nem qualquer outra lib de componentes — tudo (`Button`, `Input`,
`Select`, `Table`, `Modal`, `Drawer`, `Tabs`, `Tag`, `Alert`, `Skeleton`,
`Statistic`, `FileDropzone`, sistema de toast, ícones SVG, etc.) é
escrito à mão neste app, em CSS Modules sobre as variáveis definidas em
`src/styles/tokens.css`. Motivo: a primeira versão usava AntD e não
agradou visualmente — o pedido explícito foi trocar por componentes
próprios.

Decisões pragmáticas pra não reinventar roda onde o navegador já resolve
bem:

- **`Select`** é um `<select>` nativo estilizado — manter o
  comportamento de teclado/acessibilidade do navegador em vez de
  reimplementar um listbox.
- **`DateInput`/`DateTimeInput`** usam `<input type="date">`/
  `type="datetime-local">` nativos — sem calendário customizado.
- **`Modal`/`Drawer`** usam `createPortal` direto em `document.body`,
  fecham com `Escape` ou clique no overlay; sem gerenciamento de foco
  avançado (focus trap) — aceitável para o escopo do MVP.
- **`Table`** é genérica (`columns`/`data`/`rowKey`) com paginação
  simples (anterior/próxima + "página X de Y"), sem ordenação de coluna.

## Tema claro/escuro

`src/app/theme/ThemeContext.tsx` decide o tema inicial por
`prefers-color-scheme`, persiste a escolha do usuário em `localStorage`
e aplica via `data-theme="light"|"dark"` em `<html>`. Todo componente lê
cor/espaçamento de `var(--...)` (`src/styles/tokens.css`) — nenhum
componente teve que saber em qual tema está; só os tokens mudam de
valor entre `:root` e `[data-theme="dark"]`. O botão de alternância vive
no header (`AppLayout.tsx`).

## Estrutura

```
src/
├── app/                # httpClient (axios), queryClient, tema, layout, rotas
├── components/ui/       # kit de componentes próprio (sem lib externa)
├── modules/
│   ├── auth/            # login, sessão, ProtectedRoute
│   ├── dashboard/       # RF13
│   ├── passengers/      # RF01
│   ├── biometrics/      # RF02 (embutido no detalhe do passageiro)
│   ├── tickets/         # RF05 (embutido no detalhe do passageiro)
│   └── validations/     # RF12
├── styles/              # tokens.css (design tokens) + global.css
└── test/                # setup do Vitest
```

Cada módulo de domínio tem seu próprio `types.ts` (espelhando o schema
Pydantic do módulo equivalente na `central-api`) e `*Api.ts` (wrapper
fino sobre `httpClient`). Sem camada de "service" separada no frontend,
já que não há regra de negócio aqui além de validação de formulário.

## Autenticação

`POST /auth/login` retorna um JWT guardado em `localStorage`
(`src/modules/auth/authStorage.ts`). O `httpClient` (axios) injeta
`Authorization: Bearer <token>` em toda chamada e, num 401, limpa a
sessão e redireciona para `/login` — não há refresh token nem expiração
silenciosa tratada além disso (mesma simplicidade que
`JWT_ACCESS_TOKEN_EXPIRE_MINUTES` da central-api assume).

`AuthProvider` (`AuthContext.tsx`) faz um `GET /auth/me` ao montar a app
se já houver um token salvo, para sobreviver a um reload de página sem
forçar novo login. `ProtectedRoute` lê esse contexto e redireciona quem
não tem sessão válida para `/login`.

## Por que `VITE_API_BASE_URL=http://localhost:8000` mesmo rodando em Docker

O navegador roda na máquina do usuário, não dentro da rede do
`docker-compose` — `http://central-api:8000` (nome do serviço) não
resolveria no navegador. Por isso a env aponta para o host publicado
(`localhost:8000`), igual em dev local e em `docker compose up`.

## Dashboard (RF13)

Consome dois endpoints que não existiam antes deste módulo e foram
adicionados à `central-api` especificamente para isso:

- `GET /validations/stats` — contagem por status (`AUTHORIZED` vs.
  soma de todo o resto = negadas).
- `GET /sync/devices` — lista de dispositivos com `last_pull_at`/
  `last_push_at`; um dispositivo é marcado "Atenção" na tabela se nunca
  fez push ou não faz push há 24h+ (`STALE_THRESHOLD_HOURS` em
  `DashboardPage.tsx`) — heurística simples de UI, não um campo que a
  API calcula.

## Biometria (RF02)

`BiometricEnrollmentPanel` (embutido na aba "Biometria" do detalhe do
passageiro) oferece upload de arquivo (`FileDropzone`, próprio) OU
captura pela webcam (`WebcamCapture.tsx`, via `getUserMedia` +
`<canvas>` para um único frame — sem streaming/gravação). Em ambos os
casos o resultado é um `File` enviado como multipart para
`POST /passengers/{id}/biometrics/enroll`.

Não há preview de liveness/spoof em tempo real — o feedback (qualidade,
ou rejeição por suspeita de fraude/baixa qualidade/rosto não encontrado)
só chega depois do envio, na resposta da `central-api`. Antecipar essa
checagem no navegador exigiria rodar o `vision-service` (ou um modelo
equivalente) no cliente, fora de escopo do MVP.

## Testes

```bash
cd apps/admin-web
npm test
```

15 testes: validação dos schemas Zod (`loginSchema`, `passengerFormSchema`,
`ticketFormSchema` — inclusive a regra `valid_until > valid_from`),
`ProtectedRoute` (redireciona para `/login` sem sessão) e `LoginPage`
(mensagens de validação ao submeter vazio/e-mail inválido). Sem testes
de integração contra a `central-api` real — todos os componentes que
dependem de dados remotos (Dashboard, Passageiros, Validações) ainda não
têm teste automatizado, só verificação manual de build/lint.

`src/test/setup.ts` ainda inclui um polyfill mínimo de `window.matchMedia`
(jsdom não implementa) — não é mais só por causa de AntD: `ThemeContext`
também chama `matchMedia` pra decidir o tema inicial via
`prefers-color-scheme`, então o polyfill continua necessário.

## Rodando

```bash
cd apps/admin-web
npm install
npm run dev    # http://localhost:5173
```

Ou via `docker compose up admin-web` (depende de `central-api` já estar
no ar).

## Pendências / próximos passos

- `vite dev` é usado tanto em desenvolvimento quanto dentro do
  `docker-compose` — não há um estágio de build de produção (`vite build`
  + servidor estático/nginx) no Dockerfile, intencionalmente fora de
  escopo do MVP acadêmico.
- Sem refresh token: ao expirar o JWT, a única recuperação é logar de
  novo.
- Sem testes automatizados cobrindo as páginas que dependem de dados
  remotos (Dashboard, Passageiros, Biometria, Passagens, Validações) —
  cobertos hoje só por `tsc`/`eslint`/`vite build` e verificação manual.
- `Modal`/`Drawer` não têm focus trap completo (cliclam fora ou Escape
  fecham, mas o foco do teclado não é preso dentro do painel) —
  aceitável pro MVP, mas seria o primeiro ajuste de acessibilidade numa
  evolução pós-TCC.
- `Table` não ordena colunas por clique no cabeçalho.

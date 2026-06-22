# Vision Service

API isolada de visão computacional: detecção facial, score de qualidade,
liveness básico e geração de embedding (RF03, RF08). Não tem acesso a
banco de dados nem regra de negócio — é puramente uma API de inferência,
chamada pela `central-api` (cadastro biométrico, RF02/RF03) e pelo
`edge-api` (geração de embedding na validação de embarque, RF07/RF08).

## Stack

- **FastAPI** — camada HTTP.
- **insightface** (pacote `insightface`, modelo `buffalo_l`) — encapsula
  SCRFD (detecção) + ArcFace (reconhecimento), baixados automaticamente no
  primeiro uso.
- **OpenCV + NumPy** — decodificação de imagem e métricas de qualidade.
- **ONNX Runtime** — backend de inferência usado internamente pelo
  `insightface`.

## Pipeline (`app/pipeline/service.py`)

```
bytes da imagem
  -> decode (OpenCV)
  -> detecção de faces (FaceEngine / insightface)
  -> nenhuma face? -> face_found=false, reason=NO_FACE_DETECTED
  -> escolhe a face de maior det_score
  -> sem embedding? -> face_found=false, reason=EMBEDDING_UNAVAILABLE
  -> quality_score (app/pipeline/quality.py)
  -> liveness básico (app/pipeline/liveness.py)
  -> resposta com embedding + scores
```

## Endpoint principal

`POST /embeddings/generate` (multipart, campo `file`) — contrato consumido
por `central-api/app/modules/biometrics/vision_client.py`:

```json
{
  "face_found": true,
  "embedding": [0.1, 0.2, "...512 valores"],
  "quality_score": 0.87,
  "liveness_score": 0.91,
  "spoof_suspected": false,
  "model_name": "arcface",
  "model_version": "buffalo_l",
  "detector_name": "scrfd",
  "detector_version": "buffalo_l",
  "reason": null
}
```

`reason` possíveis: `INVALID_IMAGE`, `NO_FACE_DETECTED`,
`EMBEDDING_UNAVAILABLE`, `MULTIPLE_FACES_DETECTED` (informativo — ainda
retorna a face de maior confiança).

Outros endpoints: `GET /health`, `GET /health/models` (mostra se o modelo
já foi carregado em memória).

## Score de qualidade

Combina cinco sinais com pesos fixos (`app/pipeline/quality.py`):
confiança da detecção (20%), tamanho do rosto no frame (20%), nitidez via
variância do Laplaciano (25%), brilho médio dentro de uma faixa aceitável
(15%) e frontalidade estimada pelos 5 pontos de referência (20%).

## Liveness básico

**Não é um modelo treinado de anti-spoofing** — é heurística simples
(RFC 3.4, R2/M6: "regras básicas de consistência... arquitetura prevê
evolução para mecanismos avançados de liveness em etapas futuras"):
mede a concentração de energia em altas frequências (FFT) do recorte do
rosto. Fotos impressas ou recapturadas de tela tendem a ter picos de
frequência concentrados (moiré); uma captura direta de câmera tende a ter
uma queda de frequência mais suave. Limiar configurável via
`LIVENESS_FREQ_PEAK_RATIO_THRESHOLD`.

A `central-api` já consome esses dois campos: `BiometricService.enroll`
rejeita o cadastro e `BiometricService.compare` retorna
`DENIED_SPOOF_SUSPECTED` quando `spoof_suspected=true`.

## Download dos modelos — importante

O pacote `insightface` baixa o `buffalo_l` (detecção + reconhecimento)
automaticamente no primeiro uso, a partir da própria infraestrutura do
projeto InsightFace. **Isso exige internet de saída no primeiro boot do
container.** Depois do primeiro download, os pesos ficam em
`MODEL_ROOT` (`/app/.insightface` no container), montado como volume
nomeado (`insightface-models`) no `docker-compose.yml` — não baixa de novo
em reinicializações seguintes, só se o volume for removido.

Eu não consegui testar o download real neste ambiente (sandbox sem acesso
à maioria dos hosts de modelo). Ao rodar `docker compose up --build
vision-service` na sua máquina, acompanhe o log do primeiro boot — se o
download falhar por bloqueio de rede/firewall, é a única causa provável de
o serviço não subir.

## Testes

```bash
cd apps/vision-service
pytest
```

17 testes, todos com `FaceEngine` substituído por um fake (nenhum baixa ou
roda os modelos reais) — cobrem `quality.py`, `liveness.py` (inclusive um
caso sintético de padrão periódico para validar a heurística de spoof),
`service.py` (decisões de `reason`) e os endpoints HTTP via `TestClient`.
Não há teste de integração contra os pesos reais do `buffalo_l` — recomendo
rodar manualmente `curl -F file=@foto.jpg http://localhost:8002/embeddings/generate`
depois do primeiro boot para validar ponta a ponta.

## Pendências

- Sem testes de carga/latência (RNF01 exige ≤2s por tentativa ponta a
  ponta — vale medir com o stack completo no ar via `docker compose up`).
- Liveness é só heurística MVP; evolução para modelo treinado de
  anti-spoofing é trabalho pós-MVP (RFC 4.3).

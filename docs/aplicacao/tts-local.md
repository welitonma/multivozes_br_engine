# TTS local em CPU (Piper) — FEATURE-004

Backend alternativo ao Edge: sintetiza voz em português do Brasil **offline**,
só com CPU, usando [Piper](https://github.com/OHF-Voice/piper1-gpl) (`piper-tts`
+ `onnxruntime`). O Edge continua sendo o padrão; nada muda sem `TTS_BACKEND=piper`.

## Quando usar

- Sem internet na hora de sintetizar, ou para não depender do serviço online.
- Troca: menos natural que o Edge, menos vozes e sem estilo/emoção.

## Como ligar

```bash
pip install -r requirements-local.txt          # dependência opcional (fora da imagem)
python scripts/baixar_voz_piper.py pt_BR-faber-medium   # .onnx + .onnx.json em ./models
TTS_BACKEND=piper python main.py
```

Variáveis de ambiente (lidas pelo módulo novo, sem mexer em `main.py`/`config.py`):

| Variável | Padrão | O que faz |
| --- | --- | --- |
| `TTS_BACKEND` | `edge` | `edge` (online, padrão) ou `piper` (local). Outro valor: `RuntimeError` claro. |
| `PIPER_MODELS_DIR` | `./models` | Onde ficam os `.onnx` + `.onnx.json` (nunca versionados). |
| `PIPER_THREADS` | nº de núcleos | Threads do onnxruntime na sessão CPU. |

## Vozes

`voices_piper.json` mapeia os 6 apelidos OpenAI para modelos pt-BR (nome
desconhecido é repassado como id de modelo):

| Apelido | Modelo |
| --- | --- |
| alloy, onyx | `pt_BR-faber-medium` |
| echo, shimmer | `pt_BR-edresson-low` |
| fable, nova | `pt_BR-cadu-medium` |

Velocidade vira `length_scale = 1 / velocidade` (faixa 0.25–2.0, mesma da rota).
Pausas `[pause: Xs]` e conversão de formato (`mp3`/`wav`/`opus`) continuam no
`tts_handler` e valem para os dois backends; o silêncio usa a taxa de
amostragem do áudio gerado.

## Medida de desempenho (AC7)

Pendente: exige baixar a voz `pt_BR-faber-medium` da rede com autorização do
humano (meta: fator de tempo real < 0,5 com 2 threads irmãs do mesmo núcleo,
pior de 3 rodadas, mais pico de memória com `/usr/bin/time -v`).

## Licenças (só registro, sem decisão)

- Pacote `piper-tts==1.8.0` (verificado no `METADATA` do pacote instalado via
  PyPI em 2026-11-15): `License: GPL-3.0-or-later` (mais `Apache-2.0` num
  componente `g2pW`). É dependência **opcional** (`requirements-local.txt`),
  não entra na imagem nem no `requirements.txt`.
- Vozes pt-BR: licença a confirmar no download (não baixadas; ver AC7 acima).
  Quem decide o uso é o humano.

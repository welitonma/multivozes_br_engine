# TTS local em CPU (Piper) — FEATURE-004

Backend alternativo ao Edge: sintetiza voz em português do Brasil **offline**,
só com CPU, usando [Piper](https://github.com/OHF-Voice/piper1-gpl) (`piper-tts`
+ `onnxruntime`). O Edge continua sendo o padrão; nada muda sem `TTS_BACKEND=piper`.

## Em produção: imagem única (FEATURE-006)

A imagem Docker publicada já traz o Piper e a voz `pt_BR-faber-medium`
em `/app/models` — não é preciso instalar nada à parte. Sem `TTS_BACKEND`,
o comportamento é idêntico ao atual (Edge). Para sintetizar offline:

```bash
docker run -p 5050:5050 -e TTS_BACKEND=piper -e PIPER_THREADS=2 multivozes-br-engine
```

Para voltar ao Edge, rode a mesma imagem sem `-e TTS_BACKEND=piper`
(o padrão é `edge`).

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
| `PIPER_MODELS_DIR` | `./models` (`/app/models` na imagem) | Onde ficam os `.onnx` + `.onnx.json` (nunca versionados). |
| `PIPER_THREADS` | nº de núcleos | Threads do onnxruntime na sessão CPU. |
| `PIPER_DEFAULT_VOICE` | `pt_BR-faber-medium` | Voz usada quando a requisição omite `voice` ou informa voz do Edge. |

## Vozes

`voices_piper.json` mapeia os 6 apelidos OpenAI para modelos pt-BR (nome
desconhecido é repassado como id de modelo). Como a imagem só traz a voz
`faber`, todos os apelidos apontam para ela (não há voz Piper feminina pt-BR):

| Apelido | Modelo |
| --- | --- |
| alloy, echo, fable, onyx, nova, shimmer | `pt_BR-faber-medium` |

Além do mapa: nome **vazio** ou nome de voz do **Edge** (ex.:
`pt-BR-ThalitaMultilingualNeural`, o `DEFAULT_VOICE` atual) cai na voz padrão
(`PIPER_DEFAULT_VOICE` ou `pt_BR-faber-medium`). Assim a API sem `voice` e com
`TTS_BACKEND=piper` fala com a `faber`.

Velocidade vira `length_scale = 1 / velocidade` (faixa 0.25–2.0, mesma da rota).
Pausas `[pause: Xs]` e conversão de formato (`mp3`/`wav`/`opus`) continuam no
`tts_handler` e valem para os dois backends; o silêncio usa a taxa de
amostragem do áudio gerado.

## Medida de desempenho (AC7)

Pendente: exige baixar a voz `pt_BR-faber-medium` da rede com autorização do
humano (meta: fator de tempo real < 0,5 com 2 threads irmãs do mesmo núcleo,
pior de 3 rodadas, mais pico de memória com `/usr/bin/time -v`).

## Licenças

Ver [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md) (copiado para
dentro da imagem): `piper-tts` e `espeak-ng` (GPL-3.0-or-later), `onnxruntime`
(MIT) e voz `faber` (licença a confirmar). O humano aceitou distribuir esses
componentes na imagem pública.

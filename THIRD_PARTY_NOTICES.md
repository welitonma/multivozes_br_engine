# Avisos de terceiros

A imagem Docker desta API inclui, além do código próprio (licença MIT, ver
`LICENSE`), os seguintes componentes de terceiros. O código-fonte de cada um
está disponível nas URLs indicadas.

## piper-tts (GPL-3.0-or-later)

- Pacote: `piper-tts==1.8.0` (ver `requirements-local.txt`).
- Licença declarada no pacote: `GPL-3.0-or-later` (mais `Apache-2.0` num
  componente `g2pW`).
- Fonte: <https://github.com/OHF-Voice/piper1-gpl>

## espeak-ng (GPL-3.0-or-later, bundled no piper-tts)

- Dados de fonemização distribuídos junto do `piper-tts`.
- Licença declarada: `GPL-3.0-or-later`.
- Fonte: <https://github.com/espeak-ng/espeak-ng>

## onnxruntime (MIT)

- Dependência do `piper-tts` (motor de inferência dos modelos `.onnx`).
- Licença declarada: `MIT`.
- Fonte: <https://github.com/microsoft/onnxruntime>

## Voz `pt_BR-faber-medium` (licença a confirmar)

- Modelo de voz em português do Brasil incluído em `/app/models` na imagem.
- Dados de origem: o conjunto Hi-Fi TTS 92 é CC0; **a licença da voz
  `faber` está a confirmar**.
- Fonte: <https://github.com/rhasspy/piper>

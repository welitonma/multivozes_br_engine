# Worker Report — FEATURE-004

**Worker:** worker (pi)
**Data:** 2026-11-15
**Worktree:** `/home/weliton/Projects/multivozes_br_engine-worktrees/feat-feature-004` | **Branch:** `feat/feature-004`

## O que foi feito

Implementados os itens 1–8 da spec TTS-LOCAL (backend Piper local em CPU),
exceto a medida manual do AC7 (aguarda autorização do humano para baixar a voz
— ver Riscos). Base de testes antes de mudar: **74 passed**. Depois: **98
passed, 1 skipped** (o skip é o teste de integração real, que exige
pacote+modelo de verdade). Nenhum teste existente foi editado.

- `tts_backends/base.py` (novo): `BackendTTS(Protocol)` com
  `sintetizar_wav(texto, voz, velocidade)` e `resolver_voz(nome)`.
- `tts_backends/edge.py` (novo): `BackendEdge` com a chamada
  `edge_tts.Communicate` movida de `gerar_audio_normal` sem mudar
  comportamento; `PROXY` lido aqui.
- `tts_backends/piper.py` (novo): `BackendPiper` — cache em memória por voz,
  `PIPER_MODELS_DIR` (padrão `./models`), `PIPER_THREADS` aplicado em
  `SessionOptions().intra_op_num_threads` da sessão CPU (construção espelha o
  `PiperVoice.load` real), `length_scale = 1 / velocidade`, síntese em
  `asyncio.to_thread`, erro pt-BR claro quando falta modelo ou pacote. O
  `piper` só é importado dentro das funções.
- `voices_piper.json` (novo): alloy/onyx→`pt_BR-faber-medium`,
  echo/shimmer→`pt_BR-edresson-low`, fable/nova→`pt_BR-cadu-medium`;
  desconhecido passa direto como id de modelo.
- `requirements-local.txt` (novo): `piper-tts==1.8.0` (opcional, fora da imagem).
- `scripts/baixar_voz_piper.py` (novo): usa `piper.download_voices.download_voice`
  (baixa `.onnx` + `.onnx.json`); testado só com dublê.
- `tests/test_tts_local.py` (novo): 24 testes + 1 integração `skipif`, dublê do
  `piper`/`onnxruntime` em `sys.modules` com a mesma forma da API real
  (`PiperConfig.from_dict`, `PiperVoice(config, session, ...)`,
  `SynthesisConfig(length_scale)`, chunks com `sample_rate`+`audio_int16_bytes`,
  `SessionOptions`+`InferenceSession(path, sess_options, providers)`).
- `docs/aplicacao/tts-local.md` (novo): instalação, vozes, envs, limitações,
  AC7 pendente, licenças registradas.
- `tts_handler.py` (mudança mínima): `obter_backend_nome()` (`TTS_BACKEND`,
  erro exato `Configuração inválida: TTS_BACKEND='x' (esperado edge ou piper)`),
  `gerar_audio` desvia para `gerar_audio_piper` só com `TTS_BACKEND=piper`
  (padrão edge intacto), `gerar_audio_normal` delega ao `BackendEdge`,
  silêncio usa `frame_rate` do áudio gerado (antes 24000 fixo). Removidos
  `import edge_tts` e `PROXY` (foram para `edge.py`).
- `.gitignore`: adicionado `models/`.

API real verificada no pacote instalado via PyPI: `PiperVoice.load(model_path,
config_path=None, use_cuda=False, ...)`, `synthesize(texto, syn_config)` rende
`AudioChunk(sample_rate, sample_width=2, sample_channels=1,
audio_float_array, audio_int16_bytes, ...)`,
`SynthesisConfig(length_scale=None, ...)` (`< 1` = mais rápido).

## Arquivos alterados

(todos dentro de `allowed_paths` do contract)

- `tts_handler.py` (modificado, mínimo)
- `tts_backends/__init__.py`, `tts_backends/base.py`, `tts_backends/edge.py`,
  `tts_backends/piper.py` (novos)
- `voices_piper.json`, `requirements-local.txt`,
  `scripts/baixar_voz_piper.py`, `tests/test_tts_local.py`,
  `docs/aplicacao/tts-local.md` (novos)
- `.gitignore` (só acrescenta `models/`)

## Comandos rodados e resultado real

| # | Comando | Exit code | Output (colar trecho relevante) |
| - | ------- | --------- | ------------------------------- |
| 1 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` (base, antes) | 0 | `74 passed, 11 warnings in 15.04s` |
| 2 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` (final, sem piper-tts instalado) | 0 | `98 passed, 1 skipped, 11 warnings in 4.77s` |
| 3 | `.venv/bin/ruff check .` | 0 | `All checks passed!` |
| 4 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c "import sys; sys.path.insert(0, '.'); import tts_handler; assert 'piper' not in sys.modules"` | 0 | `(sem saída)` |
| 5 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c "import tts_handler"` (sem piper-tts instalado — `import piper` falha com `ModuleNotFoundError`, o import do handler funciona) | 0 | `lazy ok, sem piper-tts` |
| 6 | `test -z "$(git ls-files \| grep -E '\.onnx')"` | 0 | `(sem saída)` |
| 7 | `test -z "$(git status --porcelain -- main.py config.py .env.example voices.json Dockerfile requirements.txt)"` | 0 | `(sem saída)` |
| 8 | `test -z "$(find . -name __pycache__ -not -path './.venv/*' -not -path './.estrutura/*' -not -path './.ai/tmp/*')"` | 0 | `(sem saída)` |
| 9 | mutação A em cópia `.ai/tmp/mut1` (`escala = 1.0 / velocidade` → `escala = velocidade`): `pytest tests/test_tts_local.py -q -k length_scale` | 1 | `2 failed, 1 passed, 22 deselected` (`test_piper_length_scale_por_velocidade[0.5-2.0]`, `[2.0-0.5]`) |
| 10 | mutação B em cópia `.ai/tmp/mut2` (padrão `"edge"` → `"piper"`): `pytest tests/test_tts_handler.py -q` | 1 | `5 failed, 8 passed` (roteamento padrão quebrado como esperado) |
| 11 | `git diff --name-only <base>`: só `.ai/events.jsonl`, `.gitignore`, `tts_handler.py`; novos só em `allowed_paths`; `.env` inexistente | 0 | `(sem saída)` nos checks de protegidos/`.onnx` |

## Riscos ou decisões que fogem da spec

- **AC7 pendente: aguarda autorização do humano para baixar a voz.**
  Nenhum download foi feito (só PyPI para instalar/inspecionar o `piper-tts`,
  depois desinstalado para provar o AC3 sem o pacote). O script
  `scripts/baixar_voz_piper.py` foi testado só com dublê.
- **Licença (só registro, sem decisão):** `piper-tts==1.8.0` =
  `GPL-3.0-or-later` (consta no `METADATA` do pacote; mais `Apache-2.0` num
  componente `g2pW`). Dependência opcional fora da imagem. Licença das vozes
  pt-BR a confirmar no download — humano decide.
- Qualidades dos modelos em `voices_piper.json` (`medium`/`low`) seguem o
  padrão upstream do `piper-voices`; só `pt_BR-faber-medium` é confirmada pela
  spec (AC7). Se alguma der 404 no download, o script mostra a URL e o erro.
- `PIPER_THREADS` é aplicado via `intra_op_num_threads` da sessão CPU
  (o `PiperVoice.load` público não expõe a opção, então a sessão é montada
  espelhando o código-fonte dele, verificado na versão 1.8.0).
- Sem commit: humano não autorizou neste turno.

## Pronto para `CODE_REVIEW`?

- [x] Sim — `allowed_paths` respeitado, comandos acima com exit 0, decisões fora da spec declaradas
- [ ] Não — motivo:

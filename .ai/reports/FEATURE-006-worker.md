# Worker Report — FEATURE-006

**Worker:** worker (Muse Spark)
**Data:** 2026-11-15
**Worktree:** `/home/weliton/Projects/multivozes_br_engine-worktrees/feat-feature-006` | **Branch:** `feat/feature-006`

## O que foi feito

Implementados os itens 1 a 9 da spec `.specs/features/PRODUCAO-PIPER/spec.md`:

1. **Voz padrão** (`tts_backends/piper.py`, `voices_piper.json`): nova `PIPER_DEFAULT_VOICE` (padrão `pt_BR-faber-medium`) via `voz_padrao()`; `resolver_voz`: nome vazio ou voz do Edge (regex `^[a-z]{2}-[A-Z]{2}-.+Neural$`) cai na padrão; resto passa direto. Todos os 6 apelidos apontam para a `faber` (imagem só traz ela).
2. **Dockerfile**: mantém `python:3.11-slim`, ffmpeg + `libgomp1`, instala `requirements-local.txt`, baixa a voz em camada própria de cache antes do `COPY . .`, `ENV TTS_BACKEND=edge PIPER_MODELS_DIR=/app/models`, sem `PIPER_THREADS`.
3. **arm64**: `piper-tts==1.8.0` e `onnxruntime` têm wheel `manylinux aarch64` (conferido com `pip download --platform manylinux_2_28_aarch64`) → Piper instalado nas duas arquiteturas, sem `TARGETARCH`; documentado em `deploy.md`.
4. **.dockerignore**: acrescenta `models/`, `tests/`, `.github/`, `*.md` com exceção `!THIRD_PARTY_NOTICES.md`; nada de runtime ignorado (provado por AC4/AC9 com `--network none`).
5. **CI**: job `testes` (Python 3.11, `ruff check .`, `pytest -q`), `build-and-push` com `needs: testes`, label `MIT AND GPL-3.0-or-later`; gatilhos/schedule/secrets inalterados.
6. **THIRD_PARTY_NOTICES.md** criado (piper-tts/espeak-ng GPL-3.0-or-later, onnxruntime MIT, voz faber a confirmar) e linkado no README.
7. **.env.example**: `TTS_BACKEND`, `PIPER_THREADS`, `PIPER_MODELS_DIR`, `PIPER_DEFAULT_VOICE` comentadas, em português.
8. **Docs**: seção Piper em `README.md`; `tts-local.md` (imagem única, docker run, tabela de env, mapa faber, licenças) e `deploy.md` (camadas, tamanho medido, CI, voltar ao Edge).
9. **Testes** (`tests/test_tts_voz_padrao.py`, novo; anteriores sem edição): Edge/vazio→faber, apelidos→mapa, modelo passa direto, `PIPER_DEFAULT_VOICE` sobrescreve; sem rede/modelo/piper.

Sem commit (aguardando autorização do humano); sem push.

## Arquivos alterados

`tts_backends/piper.py`, `voices_piper.json`, `tests/test_tts_voz_padrao.py` (novo), `Dockerfile`, `.dockerignore`, `.github/workflows/publish.yml`, `.env.example`, `THIRD_PARTY_NOTICES.md` (novo), `README.md`, `docs/aplicacao/deploy.md`, `docs/aplicacao/tts-local.md` — todos em `allowed_paths`. (`main.py`, `config.py`, `voices.json`, `requirements.txt` intactos.)

## Comandos rodados e resultado real

> Cada linha abaixo vem de execução real com exit code, não de leitura de código.

| # | Comando | Exit code | Output (trecho relevante) |
| - | ------- | --------- | ------------------------------- |
| 1 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` | 0 | `112 passed, 1 skipped, 11 warnings in 4.75s` |
| 2 | `.venv/bin/ruff check .` | 0 | `All checks passed!` |
| 3 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c "import yaml; yaml.safe_load(open('.github/workflows/publish.yml')); print('YAML OK')"` | 0 | `YAML OK` |
| 4 | `grep -n "needs" .github/workflows/publish.yml` | 0 | `39:    needs: testes` |
| 5 | `git diff feat/feature-004 -- .github/workflows/publish.yml \| grep -E "schedule\|cron\|branches\|tags\|workflow_dispatch\|secrets\|DOCKERHUB"` | 1 | `(sem saída)` — gatilhos/schedule/secrets inalterados |
| 6 | `test -z "$(git status --porcelain -- main.py config.py voices.json requirements.txt)"` | 0 | `(sem saída)` — protegidos intactos |
| 7 | `test -z "$(git ls-files \| grep -E '\.onnx')"` | 0 | `(sem saída)` — nenhum `.onnx` versionado |
| 8 | `test -z "$(find . -name __pycache__ -not -path './.venv/*' -not -path './.estrutura/*' -not -path './.ai/tmp/*')"` | 0 | `(sem saída)` — sem `__pycache__` |
| 9 | `pip download --platform manylinux_2_28_aarch64 --python-version 3.11 --no-deps piper-tts==1.8.0 / onnxruntime` | 0 | `piper_tts-1.8.0-...-manylinux_2_28_aarch64.whl (34.1 MB)` e `onnxruntime-1.32.0-...-manylinux_2_28_aarch64.whl (23.2 MB)` baixados |
| 10 | `docker build -t multivozes-test-006 .` | 0 | `#14 DONE 9.5s` / `exporting manifest ... done`; `docker history`: apt `457MB`, pip `318MB`, voz `63.3MB` |
| 11 | `docker images` (AC2) | 0 | `multivozes-test-006:latest 1.38GB` vs `python:3.11-slim 188MB` |
| 12 | `docker run -d --name mv006-teste -p 5050:5050 -e REQUIRE_API_KEY=false multivozes-test-006` + `curl /v1/models` (AC3) | 0 | `Up 12 seconds (healthy)`; `models:200` |
| 13 | `docker run --rm --network none multivozes-test-006 python -c "from tts_handler import obter_backend_nome; ..."` (AC3) | 0 | `backend: edge` |
| 14 | síntese sem `voice`, `--network none`, `PIPER_THREADS=2`, cpuset 0,1 (AC4) | 0 | `http:200 time:0.79s bytes:26348`; ffprobe `duration=6.466757 size=26348` (>3s; RTF≈0.12) |
| 15 | síntese `voice: nova` + `[pause: 1s]` (AC4) | 0 | `http:200 time:0.32s bytes:21855`; ffprobe `duration=5.331111` (RTF≈0.06) |
| 16 | AC9 `GET /v1/models` | 0 | `http:200 bytes:77 body:'{"data":[{"id":"tts-1"...` |
| 17 | AC9 auth (`REQUIRE_API_KEY=true`, `API_KEY=teste123`) | 0 | sem chave `http:401`; errada `http:401`; certa `http:200 time:0.46s bytes:4928` |
| 18 | AC9 formatos `mp3 wav opus aac flac` | 0 | mp3 `200 11929B`; wav `200 128556B`; opus `200 24855B`; flac `200 80170B`; **aac `http:500`** — causa: `Requested output format 'aac' is not known` (ffmpeg da imagem sem muxer aac; fora do escopo, não corrigido) |
| 19 | AC9 speeds `0.5 1.0 2.0` + `3.0` | 0 | `200` com durações `7.07s > 4.05s > 2.57s` (direção certa); `3.0 → http:422` |
| 20 | AC9 pausas `[pause: 2s]` / `[pause: 700ms]` | 0 | `200`, durações `3.51s` (≥2s+fala) e `2.20s` (≥0.7s+fala) |
| 21 | AC9 `input` vazio | 0 | `http:400` |
| 22 | AC9 vozes ausente/`nova`/`onyx`/inexistente | 0 | `200` (8063B), `200` (7958B), `200` (8063B); inexistente `http:500` com mensagem clara (`Modelo Piper 'voz-que-nao-existe-xyz' não encontrado ... Baixe com: python scripts/baixar_voz_piper.py ...`) |
| 23 | AC9 2 requisições simultâneas (texto longo) + `GET /v1/models` durante | 0 | req1 `http:200 time:2.31s`, req2 `http:200 time:2.31s` (paralelo); models no meio `http:200` — síntese não bloqueia o servidor |
| 24 | AC9 texto ~2000 chars | 0 | `CHARS:2000`, `http:200 time:6.54s bytes:422051`, `duration=105.395374` (RTF≈0.062); `docker stats: cpu:0.07% mem:467.7MiB / 31.02GiB` |
| 25 | AC9 logs + `/tmp` | 0 | 4 linhas `Traceback` = só os 2 erros esperados (aac + voz inexistente, aac com chain de 2); `/tmp/tts_audio` vazio; em `/tmp` restaram só `tmph8zwalsg`+`tmpnjt36g97` do caminho de erro do aac (falha de conversão não limpa temps — comportamento pré-existente, fora do escopo); caminhos de sucesso limpos via BackgroundTasks |
| 26 | `docker rm -f mv006-teste; docker rmi multivozes-test-006 python:3.11-slim` (AC8) | 0 | `mv006-teste` removido; `grep` pós-limpeza vazio (nada restou) |
| 27 | `test ! -f .env` (AC8) | 0 | `(sem saída)` — sem `.env` |

## Ciclo de fix (FIXING, 2026-11-15)

Dois findings do review `.ai/reports/FEATURE-006-review.md`, corrigidos sem mexer em mais nada:

| # | falha | hipótese | o que mudou arquivo:linha | comando que prova |
| - | ----- | -------- | -------------------------- | ----------------- |
| 1 | Job `testes` não instalava o binário `ffmpeg`, mas `tests/test_tts_local.py` (`test_piper_formatos`, mp3/opus via `AudioSegment.from_file`) exige ffmpeg no PATH — runner sem ffmpeg quebraria o `pytest` e o `needs: testes` bloquearia todo build/push | `ubuntu-latest` traz ffmpeg hoje, mas não é contratual; pinar a instalação no workflow elimina a fragilidade | `.github/workflows/publish.yml:29-31` — novo passo `Install ffmpeg` (`sudo apt-get update && sudo apt-get install -y --no-install-recommends ffmpeg`) ANTES do passo de dependências; gatilhos/secrets/schedule/needs/label inalterados | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/publish.yml'))"` → `YAML OK` (exit 0); `grep -q 'needs' .github/workflows/publish.yml` → `needs OK` (exit 0) |
| 2 | Comentário de `requirements-local.txt` dizia "Não entram em requirements.txt nem na imagem Docker: só para uso local", desatualizado desde que o `Dockerfile` passou a instalar esse arquivo na imagem | Comentário herdado da FEATURE-004, nunca atualizado | `requirements-local.txt:1-2` — comentário corrigido para "Instalado na imagem Docker oficial (Dockerfile) e opcional na instalação manual/systemd"; linha `piper-tts==1.8.0` mantida | `cat requirements-local.txt` → comentário novo + `piper-tts==1.8.0` |

Required_checks do contract (exit codes reais, 2026-11-15): `pytest` 112 passed/1 skipped (exit 0); `ruff check .` limpo (exit 0); YAML OK (exit 0); `needs` presente; protegidos (`main.py config.py voices.json requirements.txt`) intactos; sem `.onnx`; sem `__pycache__`. Sem commit, sem push.

## Riscos ou decisões que fogem da spec

- **aac com 500**: o ffmpeg da imagem não tem o muxer `aac` (`Requested output format 'aac' is not known`). Registrado com a causa real; não corrigido (fora do escopo, item 9 da spec manda só registrar). `wav`/`mp3`/`opus`/`flac` passam.
- **Temps no caminho de erro**: a conversão aac que falha deixa 2 arquivos `tmp*` em `/tmp` (o `os.unlink` via BackgroundTasks só roda no sucesso). Comportamento pré-existente de `tts_handler.py` (fora de `allowed_paths`); só reportado.
- untracked em `git status`: `.ai/tasks/FEATURE-006.json` e `.specs/features/PRODUCAO-PIPER/` vieram da configuração do orquestrador (contract+spec), não de edição minha.

## Pronto para `CODE_REVIEW`?

- [x] Sim — `allowed_paths` respeitado, comandos acima com exit 0, decisões fora da spec declaradas
- [ ] Não — motivo:

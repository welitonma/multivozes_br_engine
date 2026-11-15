# Code Review — FEATURE-006

**Revisor:** code-reviewer (Muse Spark)
**Data:** 2026-11-15
**Branch:** `feat/feature-006` | **Base:** `feat/feature-004`
**Spec:** `.specs/features/PRODUCAO-PIPER/spec.md` | **Worker:** `.ai/reports/FEATURE-006-worker.md`

> Regra fixa: revisor nunca corrige, só reporta.

## Veredito

- [x] Aprovado — segue para `TESTING`
- [ ] Mudanças pedidas — volta para `FIXING`

Aprovação com 1 finding médio (ação recomendada, não bloqueante) e 3 infos/observações.
Evidência própria (exit codes reais, sem docker/rede/`.env`, temporários só em `.ai/tmp`):
`pytest` 112 passed/1 skipped, `ruff` limpo, YAML ok, `needs` presente, protegidos
intactos, sem `.onnx`, sem `__pycache__`, sem `.env`, 2 mutações em cópias `.ai/tmp`
matadas pelos testes novos, casos de borda do `resolver_voz` conferidos, `git check-ignore`
confirmando que nada de runtime é ignorado.

## Findings

| # | Arquivo:linha | Severidade | Descrição | Reprodução |
| - | -------------- | ---------- | --------- | ---------- |
| 1 | `.github/workflows/publish.yml:14-32` | média | Job `testes` não instala o binário `ffmpeg`, mas `tests/test_tts_local.py:240-251` (`test_piper_formatos`, mp3/opus via `AudioSegment.from_file`) exige ffmpeg no PATH. `ubuntu-latest` costuma trazer ffmpeg pré-instalado, porém isso não é contratual: se a imagem do runner mudar, `pytest -q` falha e o `needs: testes` bloqueia **todo** build/push. Ação recomendada (worker): adicionar step `sudo apt-get install -y ffmpeg` antes do pip install. Não marco como bloqueante porque os runners atuais incluem ffmpeg e o AC5 do worker passou na spec. | `grep -n "from_file\|AudioSegment" tests/test_tts_local.py` (linhas 249 e 182/235/285); job sem `apt-get` em `publish.yml:26-31`. Local: `which ffmpeg` → `/usr/bin/ffmpeg` (aqui os 112 passam por isso). |
| 2 | `requirements-local.txt:1-3` | baixa | Cabeçalho desatualizado: "Não entram em requirements.txt nem na imagem Docker: só para uso local." — o `Dockerfile:20-25` agora instala `requirements-local.txt` **dentro da imagem**. Ação: ajustar o comentário ("só para uso local" → "opcional local; incluído na imagem Docker"). | `cat requirements-local.txt` vs `git diff feat/feature-004 -- Dockerfile` |
| 3 | `.github/workflows/publish.yml:83-96` | info (risco) | Build multi-arch sob QEMU arm64 agora compila/instala `piper-tts`+`onnxruntime` aarch64 e baixa a voz em emulação — primeiro build e o rebuild semanal (`no-cache` no `schedule`) tendem a ser lentos. Mitigado pelo cache `gha`. Ação **se** estourar tempo: observar a duração do primeiro build na Actions; considerar `timeout-minutes` explícito ou (conforme spec item 3) condicional `TARGETARCH`. Sem evidência de quebra — worker provou wheels aarch64 (`pip download --platform manylinux_2_28_aarch64`, exit 0). | Leitura do workflow + relatório do worker linhas 9 e 10-11 da tabela. |
| 4 | `tts_backends/piper.py` (herdado FEATURE-004, fora do diff) | info | Observação herdada, fora do escopo: `caminho_modelo` interpola o nome da voz no path sem sanitizar (`../` escaparia de `PIPER_MODELS_DIR`); na prática só causa `RuntimeError` claro (arquivo inexistente) ou leitura de `.onnx` local. Não introduzido por esta task (pass-through é o comportamento exigido pela spec item 1c). Registro para backlog futuro, não finding desta review. | `sed -n '/def caminho_modelo/,+3p' tts_backends/piper.py` |

## Pontos verificados (foco do brief) — tudo OK

- **(a) `resolver_voz`** (`tts_backends/piper.py:105-114`): vazio/espaços/`None` → `voz_padrao()`;
  `pt-BR-ThalitaMultilingualNeural` e `pt-BR-FranciscaNeural` casam a regex
  `^[a-z]{2}-[A-Z]{2}-.+Neural$` → padrão; `alloy` → mapa (`voices_piper.json`, os 6
  apelidos → `pt_BR-faber-medium`); `pt_BR-jeff-medium`/`modelo-x` passam direto (spec 1c);
  `PIPER_DEFAULT_VOICE` (inclusive com espaços) sobrescreve. Conferido em execução real
  (ver tabela abaixo). Testes novos **matam mutações**: mutA (constante padrão trocada →
  4 failed) e mutB (regex quebrada → 2 failed), ambas em cópias `.ai/tmp/mutA|B`, originais intactos.
- **(b) Dockerfile**: `python:3.11-slim` + ffmpeg + `libgomp1` mantidos; `requirements-local.txt`
  instalado; voz baixada em camada própria **antes** do `COPY . .`; `ENV TTS_BACKEND=edge
  PIPER_MODELS_DIR=/app/models`, sem `PIPER_THREADS` ✓. `COPY . .` **não** sobrescreve
  `/app/models`: `models/` está no `.dockerignore` (contexto não contém `models/`, e COPY
  não apaga arquivos existentes). Nada de runtime ignorado: `git check-ignore` confirma
  `scripts/`, `voices_piper.json`, `voices.json`, `requirements*.txt`, `tts_backends/` presentes;
  `*.md` tem exceção `!THIRD_PARTY_NOTICES.md` (copiado para a imagem ✓). Sem segredo no Dockerfile.
- **(c) CI**: job `testes` (3.11, `requirements-dev.txt`, `ruff`, `pytest`) em PR/push;
  `build-and-push` com `needs: testes`; label `MIT AND GPL-3.0-or-later`; gatilhos, `schedule`,
  `secrets` e `push != PR` inalterados (`git diff` mostra só job+needs+label). Riscos: finding 1 (ffmpeg) e finding 3 (QEMU arm64 lento).
- **(d) THIRD_PARTY_NOTICES.md + docs**: sem afirmação jurídica além do declarado pelos pacotes
  (licenças como "declarada no pacote", fontes nas URLs); voz `faber` com "licença **a confirmar**"
  incluindo nota Hi-Fi TTS 92/CC0 ✓; português do Brasil ✓ ("ficheiro" em `piper.py` é
  pré-existente, fora do diff). Docs (`deploy.md`, `tts-local.md`, `README.md`) consistentes
  com o implementado (imagem única, `docker run -e TTS_BACKEND=piper -e PIPER_THREADS=2`, volta ao Edge, tabela de env).
- **(e) Coerência**: `main.py`, `config.py`, `voices.json`, `requirements.txt` intactos
  (`git status --porcelain` vazio); nenhum `.onnx` versionado; `.env.example` só acrescenta as 4
  vars comentadas em PT-BR; `requirements-local.txt` inalterado (ver finding 2 sobre o comentário).

## Comandos rodados e resultado real

| # | Comando | Exit code | Output (trecho relevante) |
| - | ------- | --------- | ------------------------------- |
| 1 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` | 0 | `112 passed, 1 skipped, 11 warnings in 5.09s` |
| 2 | `.venv/bin/ruff check .` | 0 | `All checks passed!` |
| 3 | `python -c "import yaml; yaml.safe_load(open('.github/workflows/publish.yml'))"` | 0 | `YAML OK` |
| 4 | `grep -n "needs" .github/workflows/publish.yml` | 0 | `39:    needs: testes` |
| 5 | `git diff feat/feature-004 --stat -- main.py config.py voices.json requirements.txt` + `git status --porcelain -- ...` | 0 | `(sem saída)` — protegidos intactos |
| 6 | `git ls-files \| grep -E '\.onnx'` | 1 (vazio) | `(sem saída)` — nenhum `.onnx` versionado |
| 7 | `find . -name __pycache__ -not -path './.venv/*' -not -path './.estrutura/*' -not -path './.ai/tmp/*'` | 0 | `(sem saída)` |
| 8 | `test ! -f .env` | 0 | `(sem saída)` — sem `.env` |
| 9 | mutA: cópia em `.ai/tmp/mutA` com `VOZ_PADRAO_PIPER` trocada + `pytest test_tts_voz_padrao.py` | 1 | `4 failed, 10 passed` — testes matam a mutação |
| 10 | mutB: cópia em `.ai/tmp/mutB` com regex quebrada + `pytest test_tts_voz_padrao.py` | 1 | `2 failed, 12 passed` — testes matam a mutação |
| 11 | `resolver_voz` casos: `''`, `'   '`, `None`, `pt-BR-Thalita…`, `pt-BR-FranciscaNeural`, `alloy`, `pt_BR-jeff-medium`, env com espaços | 0 | vazio/espaços/None/Edge→`faber`; `alloy`→`faber`; `pt_BR-jeff-medium` passa direto; env com espaços aparado |
| 12 | `git check-ignore` em scripts/voices_piper.json/voices.json/requirements*.txt/tts_backends/THIRD_PARTY_NOTICES.md | 0 | nenhum ignorado — runtime preservado |

## Checagens de escopo

- Mudanças ficaram dentro de `allowed_paths`? **Sim** — arquivos rastreados alterados
  (`tts_backends/piper.py`, `voices_piper.json`, `Dockerfile`, `.dockerignore`,
  `.github/workflows/publish.yml`, `.env.example`, `README.md`, `docs/aplicacao/deploy.md`,
  `docs/aplicacao/tts-local.md`) estão todos em `allowed_paths`; untracked
  `THIRD_PARTY_NOTICES.md` e `tests/test_tts_voz_padrao.py` também estão. (`.ai/*` e
  `.specs/` untracked/modificados são artefatos do protocolo/orquestrador, não edição do worker.)
- Algum arquivo sensível tocado (.env, credentials, etc.)? **Não** — `.env` nem existe; nenhum segredo no diff.

## Checagens de segurança (bloqueante se SIM)

- [x] Segredos/credenciais expostos (token, senha, connection string, chave)? **Não** — `publish.yml` usa os mesmos `secrets.DOCKERHUB_*` pré-existentes; `.env.example` só comenta vars sem valor.
- [x] Injeção possível (SQL, comando shell, path traversal, XSS)? **Não** (nada novo; observação herdada registrada como info nº 4).
- [x] Falha de autorização/controle de acesso (rota/função sem checar permissão)? **Não** — nenhuma rota tocada.
- [x] Dependência nova ou script de install sem revisão (RCE/supply-chain)? **Não** — `piper-tts==1.8.0`/`onnxruntime` já eram as dependências de `requirements-local.txt` (FEATURE-004); agora só entram também na imagem, com licença registrada e decisão do humano.
- [x] Log/erro vaza dado sensível? **Não** — mensagens de erro citam só nome de voz/path de modelo.

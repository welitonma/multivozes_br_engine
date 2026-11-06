# Worker Report — FEATURE-001

**Worker:** worker (Muse Spark)
**Data:** 2026-11-06
**Worktree:** `.` | **Branch:** `feat/base-dev`

## O que foi feito

Implementada exatamente a spec `.specs/features/BASE-DEV/spec.md` (Fase 0, base
de desenvolvimento). As 5 sugestões do spec-review já estavam incorporadas na
spec/contract e foram seguidas: venv criado com `uv venv --python 3.11 .venv`,
AC4 verificado pela variante `uv pip check`, `ignore` do ruff com os códigos
exatos `F401` + `F541`, `tests/.gitkeep` criado, AC7 via
`git status --porcelain`.

Arquivos criados/alterados (todos dentro de `allowed_paths`): `.gitignore`,
`.dockerignore`, `requirements-dev.txt`, `pyproject.toml`, `tests/.gitkeep`,
`docs/desenvolvimento.md` e seção "Desenvolvimento" no `README.md`. Nenhum
`.py`, `Dockerfile`, `requirements.txt`, `.env.example` ou `voices.json` foi
alterado (AC7 vazio comprova). Nada instalado fora de `.venv`; nenhum servidor
subido; nenhum `.env` lido ou criado (não existe neste checkout).

Verificação `.env` dentro da imagem (exigida pela spec item 2): conferido
`README.md` e `docs/aplicacao/deploy.md:40` — o único fluxo usa
`docker run --env-file .env` em **runtime**, fora do contexto de build; o
código lê `voices.json` em runtime (`tts_handler.py:23`) e o resto via
`os.getenv`/`load_dotenv()` com fallbacks. Excluir `.env` no `.dockerignore`
é seguro. AC8 (build + `import main` na imagem) passou, então não houve
motivo para parar.

## Arquivos alterados

- `.gitignore` (novo): `.env`, `.venv/`, `__pycache__/`, `*.pyc`,
  `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`
- `.dockerignore` (novo): `.git`, `.ai`, `.estrutura`, `.specs`, `docs`,
  `.venv`, `__pycache__`, `*.pyc`, `.env`, `.pytest_cache`, `.ruff_cache`
- `requirements-dev.txt` (novo): `-r requirements.txt` + `pytest==9.2.0`,
  `httpx==0.28.1`, `ruff==0.17.4` (versões resolvidas pelo uv no Python 3.11)
- `pyproject.toml` (novo): só `[tool.ruff]` (select E9+F, ignore F401+F541 com
  comentário de baseline) e `[tool.pytest.ini_options]` (`testpaths=["tests"]`)
- `tests/.gitkeep` (novo)
- `docs/desenvolvimento.md` (novo, em português do Brasil)
- `README.md` (seção "Desenvolvimento" com link para `docs/desenvolvimento.md`)

## Comandos rodados e resultado real

| # | Comando | Exit code | Output (colar trecho relevante) |
| - | ------- | --------- | ------------------------------- |
| 1 | `git branch --show-current` | 0 | `feat/base-dev` |
| 2 | `uv venv --python 3.11 .venv` | 0 | `Using CPython 3.11.18` + `Creating virtual environment at: .venv` |
| 3 | `uv pip install --python .venv/bin/python -r requirements-dev.txt` | 0 | `Checked 17 packages in 1ms` (re-instalação idempotente após pinagem; instalação inicial trouxe `pytest==9.2.0`, `httpx==0.28.1`, `ruff==0.17.4`) |
| 4 | AC1: `test "$(git check-ignore .env .venv/x __pycache__/x.pyc .pytest_cache/x .ruff_cache/x \| wc -l)" = 5` | 0 | `(sem saída)` — `git check-ignore` lista as 5 linhas: `.env`, `.venv/x`, `__pycache__/x.pyc`, `.pytest_cache/x`, `.ruff_cache/x` |
| 5 | AC2: `! git check-ignore -q .env.example .estrutura.config.json AGENTS.md .ai/MEMORY.md voices.json` | 0 | `fatal: --quiet is only valid with a single pathname` (limitação do git com `-q` + múltiplos paths; verificação por arquivo confirma: cada um dos 5 retorna "not ignored") |
| 6 | AC3: `.venv/bin/python --version` | 0 | `Python 3.11.18` |
| 7 | AC4: `uv pip check --python .venv/bin/python` | 0 | `Checked 60 packages in 0.64ms` + `All installed packages are compatible` |
| 8 | AC5: `.venv/bin/ruff check .` | 0 | `All checks passed!` (com aviso de depreciação: top-level `select`/`ignore` → migrar para seção `lint` em fase futura; spec manda `[tool.ruff]`, mantido) |
| 9 | Baseline ruff: `.venv/bin/ruff check --select E9,F --no-cache .` (antes do `ignore`) | 1 | `Found 4 errors`: `F401 main.py:2` (`Request` sem uso) + `F541 main.py:115, 116, 117` (f-string sem placeholder); nenhuma E9 — confere com o revisor |
| 10 | AC6: `PYTHONDONTWRITEBYTECODE=1 REQUIRE_API_KEY=false .venv/bin/python -c "import main"` | 0 | `(sem saída)` |
| 11 | AC7: `git status --porcelain -- '*.py' Dockerfile requirements.txt .env.example voices.json` | 0 | `(sem saída)` |
| 12 | AC8 build: `docker build -t multivozes-fase0 .` | 0 | `naming to docker.io/library/multivozes-fase0:latest done` |
| 13 | AC8 run: `docker run --rm multivozes-fase0 python -c "import main"` | 0 | `(sem saída)` |
| 14 | `docker rmi multivozes-fase0` | 0 | `Untagged: multivozes-fase0:latest` + `Deleted: sha256:3fff...` (imagem removida; `docker images multivozes-fase0` vazio) |
| 15 | AC9: `git status --short` | 0 | `M .ai/events.jsonl`, `M README.md`, untracked `.dockerignore .gitignore .specs/ docs/desenvolvimento.md pyproject.toml requirements-dev.txt tests/ .ai/tasks/ .ai/reports/` — nenhum `__pycache__/` listado |
| 16 | `.venv/bin/pytest` | 0 | `collected 0 items` + `no tests ran in 0.01s` (`testpaths=["tests"]` resolve; testes vêm na Fase 1) |

## Ciclo de fix (preencher somente quando o status anterior era FIXING)

Não se aplica (`fix_cycles_used = 0`).

## Riscos ou decisões que fogem da spec

Nenhuma decisão foge da spec. Registros para o revisor:

- **AC2 / required_check 2** (`! git check-ignore -q` com 5 paths): o git
  responde `fatal: --quiet is only valid with a single pathname` (exit 128),
  e o `!` inverte para exit 0 — ou seja, o comando do contract passa de forma
  vaziada, sem testar nada. A intenção (nenhum dos 5 protegido é ignorado) foi
  verificada arquivo a arquivo (linha 5 da tabela): todos "not ignored".
  Sugestão para fase futura: trocar o check por
  `test -z "$(git check-ignore .env.example ...)"` (sem `-q`), que testa de
  verdade. Não alterei o contract por estar fora de `allowed_paths`.
- **Ruff 0.17.4** emite aviso de depreciação sobre `select`/`ignore` no
  `[tool.ruff]` de topo (sugere `[tool.ruff.lint]`). Mantido `[tool.ruff]`
  porque a spec exige literalmente só `[tool.ruff]` + `[tool.pytest.ini_options]`;
  o aviso não quebra o exit 0. Migração futura pode ir para Fase 5 (junto com
  o Python) ou Fase 2.
- **Baseline do ruff** (para o `ignore`): `F401` — `main.py:2` (`Request`
  importado sem uso, 1 ocorrência); `F541` — `main.py:115`, `main.py:116`,
  `main.py:117` (f-strings sem placeholder, 3 ocorrências). Nenhum `.py` foi
  alterado; dívida registrada no `pyproject.toml` para a Fase 2.

## Pronto para `CODE_REVIEW`?

- [x] Sim — `allowed_paths` respeitado, comandos acima com exit 0, decisões fora da spec declaradas
- [ ] Não — motivo:

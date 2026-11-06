# Code Review — FEATURE-001

**Revisor:** code-reviewer (Muse Spark, sessão independente; não implementou nada)
**Data:** 2026-11-06
**Branch:** `feat/base-dev` (status confirmado `CODE_REVIEW` no contract)
**Spec:** `.specs/features/BASE-DEV/spec.md` | **Worker:** `.ai/reports/FEATURE-001-worker.md`

> Regra fixa: revisor nunca corrige, só reporta.

## Veredito

- [x] Aprovado — segue para `TESTING`
- [ ] Mudanças pedidas — volta para `FIXING`

## Reprodução própria (nada aceito do relato do worker)

Gates: `node .estrutura/ai-protocol/gates/check-gates.mjs FEATURE-001` → **OK (exit 0)**,
re-executado por mim nesta sessão (5 required_checks, todos exit 0).

| AC | Comando (reproduzido) | Exit | Resultado |
|----|------------------------|------|-----------|
| AC1 | `test "$(git check-ignore .env .venv/x __pycache__/x.pyc .pytest_cache/x .ruff_cache/x \| wc -l)" = 5` | 0 | OK, as 5 linhas listadas |
| AC2 | `! git check-ignore -q .env.example ... voices.json` | 0 | **passa de forma vaziada** (ver Finding 1); intenção verificada arquivo a arquivo: os 5 retornam "not ignored" |
| AC3 | `.venv/bin/python --version` | 0 | `Python 3.11.18` |
| AC4 | `uv pip check --python .venv/bin/python` | 0 | `All installed packages are compatible` (60 pkgs) |
| AC5 | `.venv/bin/ruff check .` | 0 | `All checks passed!` (+ aviso de depreciação, ver Finding 3) |
| AC6 | `PYTHONDONTWRITEBYTECODE=1 REQUIRE_API_KEY=false .venv/bin/python -c "import main"` | 0 | OK, sem saída |
| AC7 | `git status --porcelain -- '*.py' Dockerfile requirements.txt .env.example voices.json` | 0 | vazio |
| AC8 | `docker build -t multivozes-rev001 .` + `docker run --rm multivozes-rev001 ls -a /app` + `docker run --rm multivozes-rev001 python -c "import main"` | 0/0/0 | imagem contém `main.py`, `config.py`, `handle_text.py`, `tts_handler.py`, `utils.py`, `voices.json`; NÃO contém `.git`, `.ai`, `.estrutura`, `.specs`, `docs`, `.venv`, `.env`; `import main` exit 0. Imagem removida (`docker rmi multivozes-rev001`, exit 0) |
| AC9 | `git status --short \| grep -c __pycache__` | 0 ocorrências | OK |

Extras reproduzidos: baseline `ruff check --select E9,F --no-cache --isolated` → exatamente **4 erros**
(`F401 main.py:2`; `F541 main.py:115,116,117`; nenhum E9), idêntico ao citado;
instalação limpa em venv novo `.ai/tmp/rev-venv` (`uv venv --python 3.11` + `uv pip install -r requirements-dev.txt`,
exit 0, `uv pip check` → `All installed packages are compatible`); comandos do
`docs/desenvolvimento.md` executados literalmente no venv novo
(`ruff check .` exit 0; `pytest` → `no tests ran`, exit 5 — esperado, sem testes ainda, e o doc declara isso).

## Findings

| # | Arquivo:linha | Severidade | Descrição | Reprodução |
| - | -------------- | ---------- | --------- | ---------- |
| 1 | `.ai/tasks/FEATURE-001.json` (required_checks[1]) | info (contrato, fora de `allowed_paths`; **culpa do contrato, não do worker**) | AC2/`required_check` 2 é **vaziado**: `git check-ignore -q` com 5 paths retorna `fatal: --quiet is only valid with a single pathname` (exit 128) e o `!` inverte para exit 0 sem testar nada. A intenção foi verificada por mim arquivo a arquivo (todos "not ignored"). Também já apontado pelo worker. | `! git check-ignore -q .env.example .estrutura.config.json AGENTS.md .ai/MEMORY.md voices.json` → `fatal: --quiet is only valid...`, exit 0. Sugestão futura (orquestrador): `test -z "$(git check-ignore .env.example ...)"` sem `-q`. |
| 2 | `.gitignore:1` | baixa (sugestão; spec-cumprida — a spec pedia "no mínimo `.env`") | Variantes de segredo/ambiente **escapam**: `.env.local`, `.env.production`, `.env.test`, `foo.env` (`*.env`) e `env/` NÃO são ignorados; `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/` cobrem subpastas (testado: `sub/.venv/x` etc. ignorados). Risco real de commit acidental de `.env.local`. Sugestão Fase futura: `.env*` + `*.env` + exclusão explícita `!.env.example`. Não bloqueia (spec atendida). | `for f in .env.local .env.production .env.test foo.env env/x; do git check-ignore -q "$f" || echo "NOT-ignored: $f"; done` → todos NOT-ignored |
| 3 | `pyproject.toml:1` | info (aviso; **culpa da spec, não do worker** — a spec mandou literalmente `[tool.ruff]`) | Ruff 0.17.4 emite aviso de depreciação: `The top-level linter settings are deprecated in favour of their counterparts in the 'lint' section` (`select`/`ignore` → `[tool.ruff.lint]`). Não quebra o exit 0. Manter `[tool.ruff]` foi a decisão correta do worker (seguir a spec). Migração para `[tool.ruff.lint]` fica para Fase 2/5. `ignore` cobre só `F401`+`F541` (correto, nunca a categoria `F` inteira) — confirmado. | `.venv/bin/ruff check .` → warning + `All checks passed!`, exit 0 |
| 4 | `docs/desenvolvimento.md` | info (positivo) | Doc em PT-BR, correto e honesto: não cita `python3.11 -m venv` (declara que não documenta e por quê), não promete testes (diz que chegam na Fase 1; `pytest` com exit 5 `no tests ran` é o comportamento esperado), cita custo medido (85 MB / ~217 MB) e `ffmpeg`. Seção "Desenvolvimento" no `README.md:252-254` é só adição com link, nada mais mudou. | Leitura + execução literal no venv novo `.ai/tmp/rev-venv` |

## Checagens de escopo

- Mudanças ficaram dentro de `allowed_paths`? **Sim** — criados/alterados: `.gitignore`, `.dockerignore`, `requirements-dev.txt`, `pyproject.toml`, `docs/desenvolvimento.md`, `tests/.gitkeep`, `README.md` (só +6 linhas). `git status --porcelain -- '*.py' Dockerfile requirements.txt .env.example voices.json` vazio; demais untracked são só artefatos do protocolo (`.ai/`, `.specs/`). `pyproject.toml` tem só `[tool.ruff]` + `[tool.pytest.ini_options]`, sem `[project]`/`[build-system]`.
- Algum arquivo sensível tocado (.env, credentials, etc.)? **Não** — nenhum `.env` existe ou foi lido/criado; `requirements-dev.txt` fixa tudo com `==` (`pytest==9.2.0`, `httpx==0.28.1`, `ruff==0.17.4` + `-r requirements.txt`).

## Checagens de segurança (bloqueante se SIM)

- [ ] Segredos/credenciais expostos (token, senha, connection string, chave)? **Não** — nenhum segredo nos arquivos; `.env` excluído da imagem (fluxo documentado usa `--env-file` em runtime, `docs/aplicacao/deploy.md:40`).
- [ ] Injeção possível (SQL, comando shell, path traversal, XSS)? **Não** — nenhum `.py` mudou; escopo é só config/docs.
- [ ] Falha de autorização/controle de acesso (rota/função sem checar permissão)? **Não** — nenhuma rota tocada.
- [ ] Dependência nova ou script de install sem revisão (RCE/supply-chain)? **Não** — `requirements-dev.txt` só adiciona `pytest`, `httpx`, `ruff` pinados; instalação limpa em `.ai/tmp/rev-venv` sem conflito.
- [ ] Log/erro vaza dado sensível? **Não** — outputs contêm só versões e paths.

## Notas de higiene

- Temporários do revisor: só `.ai/tmp/rev-venv/` (ignorado por `.ai/.gitignore` → `tmp/`) e a imagem Docker `multivozes-rev001` (**removida**, `docker rmi` exit 0). Nenhum servidor subido; nenhum `.env` lido/criado; nada instalado fora de venvs; sem commit/push.

# SPEC — Base de desenvolvimento (Fase 0)

**ID:** FEATURE-001 (BASE-DEV)
**Data:** 2026-11-06
**Branch:** `feat/base-dev` (parte de `docs/estrutura-e-documentacao`, única base que já tem `.estrutura` e `.ai/`)
**Escopo:** só infraestrutura de desenvolvimento. **Nenhum `.py` da aplicação muda** e o comportamento do app não muda.

## 1. Problema

Medido em 2026-11-06:
- Não existe `.gitignore` nem `.dockerignore`: `__pycache__/` aparece como arquivo novo no `git status` ao importar o app; `.env` e `.venv/` não estão protegidos; `COPY . .` do `Dockerfile` levaria tudo para a imagem.
- Não há como instalar um ambiente de desenvolvimento reproduzível. O Python do sistema é o 3.14; o `pydantic==2.7.1` fixado não tem wheel no 3.13+, então o app só instala no **Python 3.11** (o mesmo do `Dockerfile`). Venv de 3.11 com app + pytest + httpx + ruff: 85 MB; `import main` usa ~217 MB de RAM (medido).
- Sem configuração de lint nem de pytest.

## 2. Solução

Arquivos novos (criar):

1. `.gitignore`: ignora no mínimo `.env`, `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`. **Não** pode ignorar `.env.example`, `.estrutura.config.json`, `AGENTS.md`, `.ai/**` (o `.ai/.gitignore` já cuida de `.ai/tmp/`), `voices.json`.
2. `.dockerignore`: exclui do contexto de build `.git`, `.ai`, `.estrutura`, `.specs`, `docs`, `.venv`, `__pycache__`, `*.pyc`, `.env`, `.pytest_cache`, `.ruff_cache`. **Não** pode excluir nada que o app precisa: `main.py`, `config.py`, `handle_text.py`, `tts_handler.py`, `utils.py`, `voices.json`, `requirements.txt`. O worker deve conferir no `README.md` e em `docs/aplicacao/deploy.md` se algum fluxo documentado depende de um `.env` DENTRO da imagem; se depender, **parar e avisar** (não excluir `.env` em silêncio).
3. `requirements-dev.txt`: `-r requirements.txt` + `pytest`, `httpx`, `ruff`, com as versões efetivamente resolvidas no Python 3.11 (fixar com `==`).
4. `pyproject.toml`: **só** `[tool.ruff]` e `[tool.pytest.ini_options]` (`testpaths = ["tests"]`). Sem `[project]`/`[build-system]`. Ruff: `extend-exclude` de `.estrutura`, `.ai`, `.venv`; regras `select = ["E9", "F"]`. Se o código atual violar alguma dessas regras, **não corrigir o código**: registrar cada regra violada em `ignore` com comentário `# baseline: corrigir na Fase 2 (N ocorrências)` e listar no relatório do worker as ocorrências (arquivo:linha). Baseline medida pelo revisor com `ruff check --select E9,F`: exatamente 4 violações, todas em `main.py`, nenhuma E9: `F401` (`main.py:2`, `Request` sem uso) e `F541` (`main.py:115`, `116`, `117`, f-string sem placeholder); o `ignore` deve citar esses códigos exatos (`F401`, `F541`), nunca a categoria `F` inteira. O objetivo é `ruff check .` passar hoje e a lista de dívida ficar explícita.
5. `tests/.gitkeep` (diretório vazio, para o `testpaths` do pytest apontar para algo que existe; os testes vêm na Fase 1).
6. `docs/desenvolvimento.md`: como montar o ambiente (Python 3.11 obrigatório e por quê; `uv venv --python 3.11 .venv` e `uv pip install --python .venv/bin/python -r requirements-dev.txt`; o `uv` baixa o 3.11 se faltar. NÃO documentar `python3.11 -m venv` como alternativa: o `python3.11` não está no PATH desta máquina, só o 3.14), como rodar ruff e pytest, aviso do custo medido (85 MB / ~217 MB de RAM), `ffmpeg` necessário para conversão de formato. Texto em português do Brasil.
7. `README.md` (raiz): acrescentar **uma** seção curta "Desenvolvimento" com link para `docs/desenvolvimento.md`. Nada mais no README muda.

O worker cria `.venv` (ignorado pelo git) e instala `requirements-dev.txt` nele para provar os ACs. Não instalar nada fora de `.venv`.

## 3. Critérios de aceitação (verificáveis por comando; saída e exit code no relatório)

| AC | Comando | Esperado |
|---|---|---|
| AC1 | `test "$(git check-ignore .env .venv/x __pycache__/x.pyc .pytest_cache/x .ruff_cache/x \| wc -l)" = 5` | exit 0 |
| AC2 | `! git check-ignore -q .env.example .estrutura.config.json AGENTS.md .ai/MEMORY.md voices.json` | exit 0 |
| AC3 | `.venv/bin/python --version` | `Python 3.11.x` |
| AC4 | `uv pip check --python .venv/bin/python` (o venv criado pelo `uv venv` não traz `pip`) | sem conflitos, exit 0 |
| AC5 | `.venv/bin/ruff check .` | exit 0, sem alterar `.py` |
| AC6 | `PYTHONDONTWRITEBYTECODE=1 REQUIRE_API_KEY=false .venv/bin/python -c "import main"` | exit 0 |
| AC7 | `git status --porcelain -- '*.py' Dockerfile requirements.txt .env.example voices.json` | vazio (pega também `.py` novo não rastreado) (nada da aplicação mudou) |
| AC8 | `docker build -t multivozes-fase0 .` e `docker run --rm multivozes-fase0 python -c "import main"` | exit 0 (se o daemon Docker não estiver disponível: rotular **"verificação do humano"** e descrever o roteiro; não declarar cumprido) |
| AC9 | `git status --short` após AC6 | sem `__pycache__/` listado |

## 4. Fora do escopo

Escrever testes (Fase 1), corrigir qualquer bug ou violação do ruff (Fase 2), atualizar dependências ou Python (Fase 5), CI (Fase 4), mexer em `Dockerfile`, `requirements.txt` ou `main.py`.

## 5. Riscos e decisões automáticas (revisáveis)

- **Decisão automática, revisável:** Python 3.11 como versão de desenvolvimento (igual ao `Dockerfile`; confirmado pelo humano em 2026-11-06 a atualização só na Fase 5).
- **Risco:** `.dockerignore` excluir arquivo necessário quebra a imagem. Mitigação: AC8 e a lista explícita do que não pode ser excluído.
- **Risco:** `.gitignore` esconder arquivo do protocolo. Mitigação: AC2.

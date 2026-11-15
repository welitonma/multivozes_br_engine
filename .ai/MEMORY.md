# Memória do projeto — multivozes_br_engine

> Criado por `.estrutura/scripts/link.mjs` a partir de
> `.estrutura/ai-protocol/templates/MEMORY.md`. Este arquivo é **seu** (fica no
> projeto, não no submodule) — edite à vontade. `link.mjs` nunca sobrescreve um
> MEMORY.md existente.

## Stack

- API de texto-para-fala (TTS) compatível com a API da OpenAI, usando vozes do Edge TTS (`edge-tts`).
- Python (a imagem Docker usa `python:3.11-slim`), FastAPI + Uvicorn, Pydantic, `pydub` (+ `ffmpeg`) para converter formato e inserir pausas.
- Dependências em `requirements.txt` (versões fixadas, exceto `edge-tts>=7.3.1,<8`). Desenvolvimento em `.venv` (Python 3.11, `requirements-dev.txt`): `pytest` (testes em `tests/`) e `ruff` (config em `pyproject.toml`); sem type checker. Ver `docs/desenvolvimento.md`.
- Documentação técnica da aplicação: `docs/aplicacao/README.md` (índice). Pontos de entrada: `main.py` (rotas), `tts_handler.py` (síntese).

## Comandos que sempre funcionam aqui

```
python3 -c "import ast,sys; [ast.parse(open(f).read(), f) for f in sys.argv[1:]]" main.py tts_handler.py handle_text.py config.py utils.py   # verificação de sintaxe (único required_check; sem dependências)
python main.py                                  # sobe o servidor (porta 5050 por padrão; exige dependências instaladas)
```

Com o `.venv` criado: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` e `.venv/bin/ruff check .`. Não há typecheck: não invente. O `requiredChecks` do `.estrutura.config.json` ainda é só a verificação de sintaxe (atualizar na Fase 4, com o CI).

## Convenções

- Código, nomes e documentação em português do Brasil (use "arquivo", não "ficheiro"); commits em português, estilo `tipo: descrição` (`fix:`, `docs:`, `chore:`).
- Branch por mudança; `master` é a base dos PRs. CI (`.github/workflows/publish.yml`) constrói e publica a imagem no Docker Hub.
- Não usar `git add -A`: só paths explícitos. Nunca editar nem commitar dentro de `.estrutura/` (submodule).

## Problemas conhecidos (detalhes em `docs/aplicacao/README.md`)

- Corrigidos na Fase 2 (PR em aberto): auth com `REQUIRE_API_KEY=false`, `speed` > 2.0 (agora 422), `DEFAULT_SPEED`/`DEFAULT_RESPONSE_FORMAT` (agora valem), `input` vazio (400); `DEFAULT_LANGUAGE`/`EXPAND_API` removidas; config inválida falha na inicialização.
- `voices.json` mapeia 11 das 12 vozes OpenAI para vozes que não são pt-BR (só `alloy` é pt-BR): suspeito de áudio em outro idioma em produção (a investigar).
- O `CHANGELOG.md` cita `voices.example.json`, que não existe.

## Preferências do time / do humano

- Responder em português do Brasil.
- Commit, push e PR só com confirmação do humano no turno.

<!-- PRIVATE: nunca commitar segredos aqui (tokens, senhas, .env). Para nomes
sensíveis bloqueados pelo guard, ver `.estrutura.config.json` (sensitivePatterns). -->

<!--
MEMORY.md x `elyra mem`: este arquivo é a fonte VERSIONADA de fatos do
projeto (stack, comandos, convenções; todos os agentes de qualquer ferramenta
leem). `elyra mem` é complementar, local ao Elyra deste computador e NÃO
versionado: use para preferências pessoais, decisões de sessão e fatos que
valem entre projetos (escopo global). Fato importante de projeto vai aqui (e
pode ser espelhado com `elyra mem --scope project`). Nunca segredos em nenhum
dos dois.
-->

# Memória do projeto — multivozes_br_engine

> Criado por `.estrutura/scripts/link.mjs` a partir de
> `.estrutura/ai-protocol/templates/MEMORY.md`. Este arquivo é **seu** (fica no
> projeto, não no submodule) — edite à vontade. `link.mjs` nunca sobrescreve um
> MEMORY.md existente.

## Stack

- API de texto-para-fala (TTS) compatível com a API da OpenAI, usando vozes do Edge TTS (`edge-tts`).
- Python (a imagem Docker usa `python:3.11-slim`), FastAPI + Uvicorn, Pydantic, `pydub` (+ `ffmpeg`) para converter formato e inserir pausas.
- Dependências em `requirements.txt` (versões fixadas, exceto `edge-tts>=7.3.1,<8`). Sem `pyproject.toml`, linter, type checker nem testes automatizados.
- Documentação técnica da aplicação: `docs/aplicacao/README.md` (índice). Pontos de entrada: `main.py` (rotas), `tts_handler.py` (síntese).

## Comandos que sempre funcionam aqui

```
python3 -c "import ast,sys; [ast.parse(open(f).read(), f) for f in sys.argv[1:]]" main.py tts_handler.py handle_text.py config.py utils.py   # verificação de sintaxe (único required_check; sem dependências)
python main.py                                  # sobe o servidor (porta 5050 por padrão; exige dependências instaladas)
```

Não há lint, typecheck nem test configurados: não invente comandos para eles. Se o projeto passar a ter, atualize `requiredChecks` em `.estrutura.config.json`.

## Convenções

- Código, nomes e documentação em português do Brasil (use "arquivo", não "ficheiro"); commits em português, estilo `tipo: descrição` (`fix:`, `docs:`, `chore:`).
- Branch por mudança; `master` é a base dos PRs. CI (`.github/workflows/publish.yml`) constrói e publica a imagem no Docker Hub.
- Não usar `git add -A`: só paths explícitos. Nunca editar nem commitar dentro de `.estrutura/` (submodule).

## Problemas conhecidos (detalhes em `docs/aplicacao/README.md`)

- `speed` entre 2.0 e 4.0 passa na validação da rota e gera HTTP 500 em `velocidade_para_taxa`.
- `DEFAULT_RESPONSE_FORMAT`, `DEFAULT_SPEED`, `DEFAULT_LANGUAGE` e `EXPAND_API` não têm efeito no código.
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

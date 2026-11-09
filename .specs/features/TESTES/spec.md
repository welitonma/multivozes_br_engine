# SPEC — Testes de caracterização (Fase 1)

**ID:** FEATURE-002 (TESTES)
**Data:** 2026-11-06
**Branch:** `feat/testes` (parte de `feat/base-dev`, que traz o `.venv`, o ruff e o pytest configurados)
**Escopo:** só testes e configuração de teste. **Nenhum `.py` fora de `tests/` muda.** Os bugs conhecidos NÃO são corrigidos aqui (Fase 2): entram como `xfail(strict=True)`.

## 1. Problema

O projeto não tem teste nenhum (`tests/` só tem `.gitkeep`). Sem testes, qualquer correção (Fase 2) ou atualização de dependências (Fase 5) é feita às cegas. Esta fase congela o comportamento ATUAL e registra os bugs conhecidos como falhas esperadas, de modo que a correção da Fase 2 vire a prova de que o bug existia (o `xfail` estrito falha quando o bug some, forçando remover a marca).

Fatos do código (conferir antes de usar):
- Configuração lida **na importação**: `EXIGIR_CHAVE_API`, `CHAVE_API` (via `utils.py`, importadas em `main.py`) e `REMOVER_FILTRO`, `VOZ_PADRAO` em `main.py:34-38`. Trocar `os.environ` depois do `import main` NÃO muda nada; os testes devem usar `monkeypatch.setattr(main, "NOME", valor)`.
- `utils.py` e `tts_handler.py` chamam `load_dotenv()`; `load_dotenv` não sobrescreve variável já existente no ambiente.
- `gerar_audio` é `async`; `main.text_to_speech` o chama pelo nome importado em `main` (`main.gerar_audio`). Para simular a síntese: `monkeypatch.setattr(main, "gerar_audio", falso)`. O `edge_tts.Communicate` faz rede e NUNCA pode ser chamado de verdade nos testes.
- `text_to_speech` tem `except Exception` que envolve o `HTTPException(400)` do texto vazio (`if not texto: raise HTTPException(400)` em `main.py:74-75`, dentro do `try`; `except` em `main.py:95-99`). **Medido pelo revisor da spec:** texto vazio devolve **500**, não 400 (bug B4, entra sempre).

## 2. Solução

Criar (todos em `tests/`):

1. `conftest.py`:
   - antes de qualquer import do app, atribuir de forma FORÇADA (`os.environ["X"] = ...`, não `setdefault`) `REQUIRE_API_KEY=false`, `API_KEY=teste`, `DETAILED_ERROR_LOGGING=false`, `REMOVE_FILTER=false` e `DEFAULT_VOICE=pt-BR-ThalitaMultilingualNeural`. Assim os testes não dependem de um `.env` nem do ambiente do desenvolvedor (o `load_dotenv` não sobrescreve variável já definida). Cada teste que precisa de outro valor usa `monkeypatch.setattr(main, ...)`.
   - `sys.path` para a raiz do repositório (o app não é pacote), **derivada de `__file__`** (`Path(__file__).resolve().parent.parent`), nunca caminho absoluto: o AC7 roda os testes numa cópia do repositório e um caminho absoluto faria os testes importarem o código original e nenhuma mutação falharia.
   - fixture autouse que **bloqueia rede**: `monkeypatch.setattr(socket.socket, "connect", ...)` levantando `AssertionError("rede bloqueada nos testes")`. (Prova por construção que nada chama o `edge-tts` real.)
   - fixture `client` (`fastapi.testclient.TestClient(main.app)`) e fixture `audio_falso` que troca `main.gerar_audio` por uma corrotina que (1) registra os argumentos recebidos `(texto, voz, formato, velocidade)` para os testes inspecionarem, (2) **chama `tts_handler.velocidade_para_taxa(velocidade)` antes de gravar**, exatamente como o `gerar_audio` real faz primeiro (`tts_handler.py`), de modo que `speed` fora de 0.25–2.0 levante o mesmo `ValueError` e a rota devolva o mesmo 500 do código real, e (3) grava um arquivo temporário `.mp3` com bytes `ID3` e devolve o caminho (o app apaga o arquivo depois). Sem o passo (2) o B2 seria invisível (medido: o falso simples devolve 200).
2. `test_handle_text.py`: `preparar_texto_para_tts` — emoji removido, link Markdown mantém só o texto, imagem Markdown, negrito/itálico/`~~`, código inline, bloco de código, cabeçalho `###`, tag HTML, quebras de linha e espaços múltiplos, entrada não-string devolve `""`. **Antes de escrever a asserção, execute a função e use o resultado REAL**; quando o resultado real for surpreendente (ex.: ordem das regex), registre a asserção como está e comente o porquê (`# caracteriza o comportamento atual`).
3. `test_utils.py`: `obter_env_bool` (`yes/y/true/1/t` em qualquer caixa → True; `0/false/no/off/""` → False; variável ausente → padrão) e `TIPOS_MIME_AUDIO`.
4. `test_tts_handler.py`: `velocidade_para_taxa` (0.25, 1.0, 1.5, 2.0; 0.24 e 2.01 levantam `ValueError`); `gerar_audio` com `asyncio.run` (sem `pytest-asyncio`): apelido (`alloy`) é traduzido pelo `MAPEAMENTO_VOZES`, voz desconhecida passa direto, texto com `[pause: 1s]` (qualquer caixa) vai para `gerar_audio_com_pausas`, texto sem pausa vai para `gerar_audio_normal` (as duas funções trocadas por falsos via `monkeypatch`); `voices.json` carrega e tem `alloy`.
5. `test_api.py` (via `TestClient`, `main.gerar_audio` falso):
   - `GET /v1/models` → 200 com `tts-1` e `tts-1-hd`, sem cabeçalho.
   - `POST /v1/audio/speech` feliz → 200, `content-type` `audio/mpeg`, corpo não vazio, e o arquivo temporário foi apagado depois da resposta.
   - Autenticação com `main.EXIGIR_CHAVE_API=True` e `main.CHAVE_API="segredo"`: chave certa → 200; chave errada → 401; **sem cabeçalho → 401 ou 403** (hoje 403 com as versões fixadas; 401 em Starlette novo; aceitar os dois); `CHAVE_API=None` → 500.
   - Texto vazio: o teste de caracterização afirma o status REAL (500) e o B4 (item 6) afirma o correto (400) como `xfail`.
   - `response_format` desconhecido cai em `audio/mpeg`; `response_format=wav` → `audio/wav`.
6. **Bugs conhecidos como `xfail(strict=True, reason="...")`**, cada um com o teste que descreve o comportamento CORRETO:
   - (B1) `REQUIRE_API_KEY=false` (`main.EXIGIR_CHAVE_API=False`) e **sem** cabeçalho `Authorization` → deveria ser 200 (hoje 403).
   - (B2) `speed=3.0` → deveria ser 422 (validação clara); hoje 500 por causa de `velocidade_para_taxa` (o `ValueError` cai no `except` genérico). Só é observável porque o `audio_falso` replica a chamada a `velocidade_para_taxa` (ver item 1).
   - (B3) `DEFAULT_SPEED` / `DEFAULT_RESPONSE_FORMAT` lidas e ignoradas (`main.py:36-37`): com `main.VELOCIDADE_PADRAO=1.5` e requisição sem `speed`, a velocidade enviada a `gerar_audio` deveria ser 1.5 (hoje sempre 1.0). Idem formato com `main.FORMATO_RESPOSTA_PADRAO="wav"` sem `response_format`.
   - (B4) `input: ""` → deveria ser 400; hoje 500, porque o `HTTPException(400)` (`main.py:74-75`) é capturado pelo `except Exception` (`main.py:95-99`) e reempacotado. Medido pelo revisor da spec; entra sempre.
   Cada `xfail` tem `reason` citando arquivo:linha e `docs/aplicacao/README.md` (item correspondente).

Ajustes de configuração herdados da Fase 0 (a revisão apontou, não bloqueantes):
7. `.gitignore`: acrescentar `.env.*` e a exceção `!.env.example`, para cobrir `.env.local`, `.env.production` etc. sem esconder o exemplo.
8. `pyproject.toml`: mover `select` e `ignore` do ruff para `[tool.ruff.lint]` (o ruff 0.17.4 avisa a depreciação); manter o baseline F401/F541.
9. `docs/desenvolvimento.md`: trocar o trecho que hoje diz "os testes chegam na Fase 1" (linha 30 de `docs/desenvolvimento.md`) pelo texto real: como rodar (`.venv/bin/pytest -q`), o que significa `xfail`, que a rede é bloqueada nos testes e como adicionar um teste.

NÃO instalar dependência nova (nada de `pytest-asyncio`, `pytest-cov`, `respx`...). Só pytest, httpx e o que já está em `requirements-dev.txt`.

## 3. Critérios de aceitação (saída e exit code reais no relatório)

| AC | Comando | Esperado |
|---|---|---|
| AC1 | `.venv/bin/pytest -q` | exit 0; linha final com `passed` e `xfailed` (≥ 4), `0 failed`, `0 error`, nenhum `xpassed` |
| AC2 | `.venv/bin/pytest -q -rx` | os xfails listados com motivo (B1, B2, B3 e B4) |
| AC3 | `env -u REQUIRE_API_KEY -u API_KEY .venv/bin/pytest -q` e uma 2ª rodada com `REQUIRE_API_KEY=true API_KEY=x` exportados | exit 0 nas duas (testes não dependem do ambiente do desenvolvedor; a 2ª rodada tem que EXPORTAR as variáveis antes de chamar o `pytest`, porque a configuração é lida na importação — `monkeypatch` aqui não prova nada) |
| AC4 | `.venv/bin/ruff check .` e `.venv/bin/ruff check . 2>&1 \| grep -ci deprecated` | exit 0 e `0` |
| AC5 | `git status --porcelain -- '*.py' ':!tests'` | vazio (nenhum `.py` da aplicação mudou) |
| AC6 | `git check-ignore -q .env.local` e `... .env.production` (um por vez) | exit 0; e `.env.example` NÃO ignorado (exit 1) |
| AC7 | **Mutação:** numa CÓPIA do repositório em `.ai/tmp/` (nunca no original), quebrar `velocidade_para_taxa` (ex.: limite 2.0 → 4.0), a regex de link em `handle_text.py` e o mapeamento de voz; rodar `pytest -q` na cópia | cada mutação derruba pelo menos um teste; registrar qual |
| AC8 | **Rede bloqueada:** em cópia, trocar `main.gerar_audio` por chamada real ao `edge_tts` | os testes que a usam falham com "rede bloqueada" (prova que a fixture funciona) |
| AC9 | `.venv/bin/pytest --collect-only -q \| tail -3` | lista os testes coletados (≥ 25) |

## 4. Fora do escopo

Corrigir qualquer bug (Fase 2), cobertura de conversão real de formato com `ffmpeg`, testes de integração com rede/Docker, CI (Fase 4), atualizar dependências (Fase 5), mexer em `main.py`, `tts_handler.py`, `handle_text.py`, `utils.py`, `config.py`.

## 5. Riscos e decisões automáticas (revisáveis)

- **Decisão automática:** sem `pytest-asyncio` (`asyncio.run` basta e evita dependência nova).
- **Decisão automática:** autenticação sem cabeçalho aceita 401 ou 403, para o teste não quebrar por causa da diferença Starlette 0.37 vs 1.x (a Fase 5 não deve ser barrada por isso).
- **Risco:** teste que descreve um comportamento por acidente (ex.: ordem das regex) vira trava de refatoração. Mitigação: comentário `# caracteriza o comportamento atual` para esses casos.
- **Risco:** `xfail` estrito que passa por acidente. Mitigação: AC1 exige 0 `xpassed`.

# Worker Report — FEATURE-002

**Worker:** worker (pi)
**Data:** 2026-11-06
**Worktree:** `.` | **Branch:** `feat/testes`

## O que foi feito

Implementada exatamente a spec `.specs/features/TESTES/spec.md` (rodada 2 aprovada):

- `tests/conftest.py` — env forçado (`os.environ[...] =`, nunca `setdefault`), `sys.path` por `Path(__file__).resolve().parent.parent`, fixture autouse que bloqueia `socket.socket.connect` com `AssertionError`, fixtures `client` e `audio_falso` (registra `(texto, voz, formato, velocidade)`, chama `tts_handler.velocidade_para_taxa` antes de gravar, devolve `.mp3` temporário com bytes `ID3`).
- `tests/test_handle_text.py` (13 testes) — asserções escritas a partir do resultado REAL medido (`.ai/tmp/probe002.py`); caso surpreendente comentado (`![alt](...)` → `"!alt"`, a regra de link roda antes da de imagem — `# caracteriza o comportamento atual`).
- `tests/test_utils.py` — `obter_env_bool` (verdadeiros/falsos/ausente) + `TIPOS_MIME_AUDIO` integral.
- `tests/test_tts_handler.py` — `velocidade_para_taxa` (4 válidos + 2 inválidos), 3 corrotinas, roteamento normal/pausas (incl. caixa alta), `voices.json` tem `alloy`.
- `tests/test_api.py` (14 testes) — modelos, feliz (200 + `audio/mpeg` + corpo + temporário apagado), auth (certa 200 / errada 401 / sem cabeçalho 401-ou-403 / `CHAVE_API=None` 500), texto vazio real (500), formatos `xyz`→`audio/mpeg` e `wav`→`audio/wav`, B1–B4 como `xfail(strict=True)` com `reason` citando arquivo:linha + `docs/aplicacao/README.md`.
- `.gitignore` — acrescentados `.env.*` e `!.env.example`.
- `pyproject.toml` — movidos SÓ `select` e `ignore` para `[tool.ruff.lint]`; `extend-exclude` permanece em `[tool.ruff]` (sugestão 1 do revisor).
- `docs/desenvolvimento.md` — linha 30 ("os testes chegam na Fase 1") trocada por: como rodar, o que os testes cobrem, `xfail` estrito, rede bloqueada, como adicionar teste.
- Nenhum `.py` fora de `tests/` alterado; sem dependência nova; sem rede real; sem `.env` lido/criado; `PYTHONDONTWRITEBYTECODE=1` em todas as execuções; temporários só em `.ai/tmp/`.

## Arquivos alterados

Todos dentro de `allowed_paths` (`tests/**`, `pyproject.toml`, `.gitignore`, `docs/desenvolvimento.md`):

- `tests/conftest.py` (novo), `tests/test_handle_text.py` (novo), `tests/test_utils.py` (novo), `tests/test_tts_handler.py` (novo), `tests/test_api.py` (novo)
- `pyproject.toml`, `.gitignore`, `docs/desenvolvimento.md`

## Comandos rodados e resultado real

| # | Comando | Exit code | Output (colar trecho relevante) |
| - | ------- | --------- | ------------------------------- |
| 1 | AC1: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` | 0 | `55 passed, 5 xfailed, 7 warnings in 0.10s` (0 failed, 0 error, 0 xpassed) |
| 2 | AC2: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -rx` | 0 | `XFAIL tests/test_api.py::test_b1_...`, `test_b2_...`, `test_b3_velocidade...`, `test_b3_formato...`, `test_b4_...` + `55 passed, 5 xfailed` |
| 3 | AC3a: `env -u REQUIRE_API_KEY -u API_KEY .venv/bin/pytest -q` | 0 | `55 passed, 5 xfailed, 11 warnings in 0.14s` |
| 4 | AC3b: `export REQUIRE_API_KEY=true API_KEY=x; .venv/bin/pytest -q` (export ANTES do pytest — sugestão 2 do revisor) | 0 | `55 passed, 5 xfailed, 7 warnings in 0.10s` |
| 5 | AC4a: `.venv/bin/ruff check .` | 0 | `All checks passed!` |
| 6 | AC4b: `.venv/bin/ruff check . 2>&1 \| grep -ci deprecated` | 0 | `0` |
| 7 | AC5: `git status --porcelain -- '*.py' ':!tests'` | 0 | `(sem saída)` |
| 8 | AC6: loop `check-ignore` do contract | 0 | `.env.local` e `.env.production` ignorados; `.env.example` e `tests/test_api.py` NÃO ignorados (`check-ignore ok`) |
| 9 | AC7a mutação vel (`tto_handler 2.0→4.0` em `.ai/tmp/ac7-vel`): `pytest -q` | 0 (do pytest: 1 failed) | `FAILED tests/test_tts_handler.py::test_velocidade_para_taxa_invalidos[2.01]` + `1 failed, 54 passed, 5 xfailed` |
| 10 | AC7b mutação link (regex em `.ai/tmp/ac7-link`): `pytest -q` | 0 (do pytest: 3 failed) | `FAILED test_link_markdown_mantem_texto`, `test_imagem_markdown_mantem_alt_com_exclamacao`, `test_imagem_no_meio_de_frase` + `3 failed, 52 passed, 5 xfailed` |
| 11 | AC7c mutação voz (`alloy`→`voz-MUTANTE` em `.ai/tmp/ac7-voz`): `pytest -q` | 0 (do pytest: 2 failed) | `FAILED test_gerar_audio_traduz_apelido`, `test_voices_json_tem_alloy` + `2 failed, 53 passed, 5 xfailed` |
| 12 | AC8 rede (conftest da cópia `.ai/tmp/ac8-rede` chama o `gerar_audio` real): `pytest -q` | 0 (do pytest: 4 failed) | `FAILED test_speech_feliz`, `test_auth_chave_certa`, `test_formato_desconhecido_cai_em_mpeg`, `test_formato_wav` (`assert 500 == 200`) + `4 failed, 51 passed, 5 xfailed`; contador de chamadas a `socket.socket.connect` no caminho real = 2 (fixture intercepta; nada sai à rede) |
| 13 | AC9: `.venv/bin/pytest --collect-only -q \| tail -3` | 0 | `60 tests collected in 0.04s` (60 = 55 passed + 5 xfailed) |
| 14 | required_check: `test "$(.venv/bin/ruff check . 2>&1 \| grep -ci deprecated)" = 0` | 0 | `deprecated=0 ok` |
| 15 | required_check: `test -z "$(git status --porcelain -- '*.py' ':!tests')"` | 0 | `vazio ok` |

Notas sobre exit codes: nas linhas 9–12 o "exit 0" é do pipeline `grep` (o pytest na cópia sai 1 por design — a mutação/ rede derruba testes, que é o esperado e prova o AC). Na árvore principal o pytest sai 0 (linha 1).

## Ciclo de fix (preencher somente quando o status anterior era FIXING)

Não se aplica (status anterior `READY_FOR_IMPLEMENTATION`, `fix_cycles_used=0`).

## Riscos ou decisões que fogem da spec

Nenhuma decisão foge da spec. Dois registros (sem correção no app, conforme a regra):

1. **AC8 — erro visível não é o texto "rede bloqueada":** com as versões fixadas (`aiohttp` + `aiohappyeyeballs`), o `AssertionError("rede bloqueada nos testes")` levantado no `socket.socket.connect` é engolido pela camada happy-eyeballs e emerge como `IndexError: list index out of range` → `RuntimeError` → HTTP 500. A prova de que a fixture funciona: (a) os 4 testes que usam síntese falham (`500 == 200`) só na cópia com o `gerar_audio` real; (b) contador instrumentado mostra `socket.socket.connect` chamado 2x pelo caminho real — ou seja, a tentativa de rede é interceptada antes de sair. Nenhum teste da árvore principal depende desse texto.
2. **`![alt](...)` → `"!alt"` (não `"alt"`):** ordem das regex em `handle_text.py` (link antes de imagem) deixa o `!` sobrando. Congelado como está, com comentário `# caracteriza o comportamento atual`, sem tocar no app.

## Pronto para `CODE_REVIEW`?

- [x] Sim — `allowed_paths` respeitado, comandos acima com exit 0, decisões fora da spec declaradas
- [ ] Não — motivo:

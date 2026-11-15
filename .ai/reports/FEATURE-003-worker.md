# Worker Report — FEATURE-003

**Worker:** worker (sessão Elyra, branch `fix/correcoes`)
**Data:** 2026-11-14
**Worktree:** `.` | **Branch:** `fix/correcoes`

## O que foi feito

Implementados os itens 1–9 da spec `.specs/features/CORRECOES/spec.md`:

1. **B1** (`main.py`): `security = HTTPBearer(auto_error=False)`; `verificar_chave_api` recebe `credentials: HTTPAuthorizationCredentials | None`. Ordem: `EXIGIR_CHAVE_API` falso → retorna; `CHAVE_API` ausente → 500 (primeiro, mesmo sem cabeçalho); `credentials is None` (ausente ou esquema ≠ Bearer) → 401 com `WWW-Authenticate: Bearer`; chave errada → 401 com o mesmo cabeçalho.
2. **B2** (`main.py`): `speed` com `le=2.0`, descrição "0.25 a 2.0". Fora da faixa → 422 do Pydantic.
3. **B3** (`main.py`): `speed` e `response_format` passam a `None` por padrão (`float | None` com `ge/le`, `str | None`); na rota, `None` → `VELOCIDADE_PADRAO` / `FORMATO_RESPOSTA_PADRAO`. Valor enviado sempre vence.
4. **B4** (`main.py`): `except HTTPException: raise` antes do `except Exception` — `input` vazio → 400. Texto que só esvazia após o filtro (só emoji) mantém o comportamento atual (200, medido) e foi registrado em teste de caracterização novo.
5. **Variáveis mortas**: `DEFAULT_LANGUAGE` removida de `config.py`; bloco `DEFAULT_LANGUAGE` e bloco `EXPAND_API` (com comentários) removidos do `.env.example`.
6. **Validação na importação** (`main.py`, onde `TIPOS_MIME_AUDIO` já é importado; sem helper em `utils.py`): `PORT` não inteiro ou fora de 1–65535, `DEFAULT_SPEED` não numérico ou fora de 0.25–2.0, `DEFAULT_RESPONSE_FORMAT` fora das chaves de `TIPOS_MIME_AUDIO` → `RuntimeError` (stderr) com prefixo exato `Configuração inválida: NOME='valor'` + esperado.
7. **Baseline do ruff**: removidos `Request` (`main.py`), `f` sem placeholder em 3 `print` (`main.py`), `import os` sem uso (`tests/test_utils.py`); bloco `ignore` **inteiro com os comentários** apagado do `pyproject.toml` (sem `F401`/`F541` nem em comentário — S1).
8. **Testes** (`tests/test_api.py`): 5 marcas `xfail` removidas; caracterizações ajustadas (vazio 500→400; "401 ou 403"→401); novos: limites 2.0/0.25 aceitos, 2.01/0.24→422 com campo `speed` no detalhe, cliente-vence-padrão (×2), chave errada/Basic/sem cabeçalho→401 com `WWW-Authenticate` (chegada ligada), sem-`CHAVE_API`+sem-cabeçalho→500, caracterização só-emoji (200, comportamento real medido), config inválida em subprocesso (6 casos, env mínimo explícito, sem `-I`), variáveis mortas lendo só `config.py`+`.env.example`.
9. **Docs**: `docs/aplicacao/` (main.md, README.md, tts-handler.md l.28-29/121-122, texto-config-utils.md, deploy.md) + `docs/desenvolvimento.md` (trecho `xfail` no passado). Bugs B1–B4 passam a "corrigido na Fase 2"; itens de lacuna 1–4 e 14 riscados com a correção. Nomes literais `DEFAULT_LANGUAGE`/`EXPAND_API` zerados nos docs (AC8 grep1 vazio; itens 3–4 reescritos sem os literais).

Sugestões do revisor atendidas: S1 (bloco `ignore` inteiro removido), S2 (`./__pycache__` pré-existente removido via `shutil.rmtree`, sem `rm -rf`; `PYTHONDONTWRITEBYTECODE=1` em todo comando Python), S3 (teste de caracterização só-emoji acrescentado com comportamento real medido: 200 + `gerar_audio` chamado com `''`).

Sem commit (exige confirmação humana). Sem `.env` lido/criado; sem rede; sem servidor. Temporários só em `.ai/tmp/`.

## Arquivos alterados

Todos dentro de `allowed_paths`: `main.py`, `config.py`, `.env.example`, `pyproject.toml`, `tests/test_api.py`, `tests/test_utils.py`, `docs/aplicacao/main.md`, `docs/aplicacao/README.md`, `docs/aplicacao/tts-handler.md`, `docs/aplicacao/texto-config-utils.md`, `docs/aplicacao/deploy.md`, `docs/desenvolvimento.md`. `utils.py`, `tts_handler.py`, `handle_text.py`, `Dockerfile`, `requirements*.txt`, `voices.json` intactos.

## Comandos rodados e resultado real

| # | Comando | Exit code | Output (colar trecho relevante) |
| - | ------- | --------- | ------------------------------- |
| 1 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` | 0 | `74 passed, 7 warnings in 2.32s` (0 failed, 0 xfailed, 0 xpassed) |
| 2 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest --collect-only -q \| grep -c '::'` | 0 | `74` (≥ 60) |
| 3 | `.venv/bin/ruff check .` | 0 | `All checks passed!` |
| 4 | `.venv/bin/ruff check --select E9,F --no-cache --isolated .` | 0 | `All checks passed!` |
| 5 | `test -z "$(grep -n 'ignore' pyproject.toml)"` | 0 | `(sem saída)` |
| 6 | `grep -nE "ignore\|F401\|F541" pyproject.toml` | 1 | `(sem saída — vazio, como exigido)` |
| 7 | `test -z "$(grep -rn 'xfail(' tests/)"` | 0 | `(sem saída)` |
| 8 | loop vars mortas nos 6 arquivos (`main.py config.py utils.py tts_handler.py handle_text.py .env.example`) | 0 | `(sem saída — nenhuma variável morta)` |
| 9 | `test -z "$(git status --porcelain -- Dockerfile requirements.txt requirements-dev.txt voices.json)"` | 0 | `(sem saída — intactos)` |
| 10 | AC6 antes: `out=$(PORT=abc ... import main); echo rc; grep "Configuração inválida: PORT='abc'"` | 1 (grep) | `rc=1`, `ValueError: invalid literal for int() with base 10: 'abc'` — trecho ausente (negativo confirmado) |
| 11 | AC6 depois PORT: `test $rc -ne 0 && echo "$out" \| grep -q "Configuração inválida: PORT='abc'"` | 0 | OK |
| 12 | AC6 depois SPEED: `... grep -q "Configuração inválida: DEFAULT_SPEED='9'"` | 0 | OK |
| 13 | AC5 mut-b1 (volta `HTTPBearer()`): pytest na cópia `.ai/tmp/mut-b1` | 1 | `5 failed, 69 passed` — `test_b1_sem_cabecalho_com_checagem_desligada`, `test_auth_sem_cabecalho` (403≠401), `test_auth_esquema_basic_rejeitado`, `test_auth_sem_chave_configurada_sem_cabecalho` (+ `test_variaveis_mortas_removidas`, artefato da cópia sem `.env.example`) |
| 14 | AC5 mut-b2 (volta `le=4.0`): pytest na cópia `.ai/tmp/mut-b2` | 1 | `3 failed, 71 passed` — `test_b2_speed_3_devolve_422` (500≠422), `test_speed_fora_dos_limites_devolve_422` (+ artefato da cópia) |
| 15 | AC5 mut-b3 (ignora padrões): pytest na cópia `.ai/tmp/mut-b3` | 1 | `10 failed, 64 passed` — `test_b3_velocidade_padrao_respeitada`, `test_b3_formato_padrao_respeitado` e outros com 500 por `None` (+ artefato da cópia) |
| 16 | AC5 mut-b4 (remove `except HTTPException: raise`): pytest na cópia `.ai/tmp/mut-b4` | 1 | `3 failed, 71 passed` — `test_b4_texto_vazio_devolve_400`, `test_texto_vazio_devolve_400` (500≠400) (+ artefato da cópia) |
| 17 | `git grep -n "DEFAULT_LANGUAGE\\|EXPAND_API" -- docs/aplicacao/ docs/desenvolvimento.md .env.example config.py` | 1 | `(sem saída — vazio)` |
| 18 | AC8 grep2 (revisão manual): `git grep -n -i -E "bug conhecido\|ainda não corrigid\|lacuna\|sem uso\|sem efeito\|discrepância\|403" -- docs/aplicacao/ docs/desenvolvimento.md` | 0 | Resíduos revisados: título "Lacunas conhecidas e discrepâncias", itens riscados 1–4/14 com "corrigido na Fase 2", "Discrepância" do changelog em `docs-existentes.md:141` (Fase 3, fora do escopo), nota histórica em `main.md:74-75` (com "corrigido na Fase 2"). Nenhum resíduo afirma que B1–B4 seguem abertos. |
| 19 | S3 medição real: POST só-emoji via TestClient | 0 | `status: 200`, `chamadas: [('', 'pt-BR-ThalitaMultilingualNeural', 'mp3', 1.0)]` → registrado no teste |
| 20 | `test -z "$(find . -name __pycache__ -not -path './.venv/*' -not -path './.estrutura/*' -not -path './.ai/tmp/*')"` + `test ! -e .env` | 0 | OK (ambos) |
| 21 | `git diff --name-only` (AC7) | 0 | Só `allowed_paths` + `.ai/events.jsonl` (artefato do protocolo) |

## Riscos ou decisões que fogem da spec

- Nenhuma decisão fora da spec. Observação: no teste de mutação, `test_variaveis_mortas_removidas` falha nas cópias por `FileNotFoundError` (a cópia mínima não inclui `.env.example`) — artefato do harness de mutação, não da correção; cada mutação derruba testes-alvo reais mesmo sem contar esse.
- O teste de subprocesso usa env mínimo exato da spec (`PATH`, `PYTHONDONTWRITEBYTECODE=1`, `REQUIRE_API_KEY=false`, `API_KEY=teste` + variável do caso).

## Ciclo de fix — correção 1 (2026-11-14, escopo fechado: só números de linha nos docs)

- Falha que gerou o retorno (onde está em `-review.md`): findings 1–9 de `.ai/reports/FEATURE-003-review.md` — "Para o worker": ~20 referências de linha em 4 docs apontavam para linhas antigas do `main.py`/`.env.example`.
- Hipótese da causa: o `main.py` cresceu ~24 linhas na Fase 2 (validação de config) e o `.env.example` perdeu os blocos `DEFAULT_LANGUAGE`/`EXPAND_API`; os docs mantiveram os números antigos.
- O que mudou (arquivo:linha): ver lista abaixo (só `docs/aplicacao/**`, nenhuma mudança de código/comportamento/testes).
- Comando que prova a correção (com exit code): `grep -rn "main.py:" docs/` + `grep -rn "env.example:" docs/` conferidos contra `grep -n`/`sed -n` no `main.py` e `.env.example` atuais (exit 0); `node .estrutura/ai-protocol/gates/check-gates.mjs FEATURE-003` → `RESULTADO: OK`, exit 0 (2ª rodada, após o evento de transição).

Motivo (review findings 1–9): código B1–B4/validação/testes/ruff OK; ~20 referências de linha em 4 docs apontavam para linhas antigas do `main.py`/`​.env.example` (cresceu ~24 linhas). Nenhuma mudança de código, comportamento ou testes — só `docs/aplicacao/**`.

Conferência real antes de escrever (`grep -n`/`sed -n` no `main.py` e `.env.example` atuais — não confiei cegamente no mapa; todos os valores do mapa confirmaram):

- `text_to_speech` `89–122` (def 89, `FileResponse` 115, fim `except` 122); 400 do `input` em `95–97`; `VOZ_PADRAO` 41; filtro `100–101`; MIME `104–107`; `gerar_audio` 110; `unlink` 113; `FileResponse` 115; `listar_modelos` `126–131` (decorator 126, def 127, return 131); bloco config `34–52` (`_PORT_BRUTO` 34, `PORTA=int` 36, faixa 39–40, `VOZ_PADRAO` 41, `FORMATO_RESPOSTA_PADRAO` 42, `_VELOCIDADE_BRUTA` 45, `VELOCIDADE_PADRAO` 47, `REMOVER_FILTRO` 52); `uvicorn.run` 146; banner `135–146` (`if __name__` 135 → `uvicorn.run` 146); `.env.example`: `REMOVE_FILTER` 36, `DETAILED_ERROR_LOGGING` 40, `PROXY` 43 (linha única comentada).
- Mantidas como corretas (revisor): `TTSRequest` `21–28`, `:28`, `load_dotenv` `:31`, imports `1–16`; `docs/desenvolvimento.md` sem refs `main.py:` (nada a corrigir).

O que mudou (arquivo:linha do doc → antes → depois):

- `docs/aplicacao/main.md`: `66-99`→`89-122`; `71-73`→`95-97`; `VOZ_PADRAO :81`→`:41`; `75-77`→`100-101`; `81-85`→`104-107`; `:88`→`:110`; `:91`→`:113`; `:93`→`:115`; `listar_modelos 102-108`→`126-131`; `34-38`→`34-52`; `uvicorn :122`→`:146`; banner `111-122`→`135-146`.
- `docs/aplicacao/texto-config-utils.md`: `:77`→`:100-101`; `34-38`→`34-52`; tabela `PORT :34`→`:36,39-40`, `DEFAULT_VOICE :35`→`:41`, `DEFAULT_RESPONSE_FORMAT :36`→`:42`, `DEFAULT_SPEED :37`→`:45,47`, `REMOVE_FILTER :38`→`:52`.
- `docs/aplicacao/tts-handler.md`: `:88`→`:110`; `:91`→`:113`.
- `docs/aplicacao/deploy.md`: `REMOVE_FILTER :40`→`:36`; `DETAILED_ERROR_LOGGING :44`→`:40`; `PROXY :51-52`→`:43`.

Saída do gate:

- 1ª rodada (antes do evento de transição): `node .estrutura/ai-protocol/gates/check-gates.mjs FEATURE-003` → 9 `required_checks` OK (`74 passed`, ruff OK), mas `RESULTADO: FALHOU`, exit 1, só pelo gate anti-silêncio (`deploy.md mudou depois do ultimo evento ... Registre um evento antes de prosseguir`) — esperado antes da transição `FIXING → CODE_REVIEW`.
- 2ª rodada (após `validate-task-state ... CODE_REVIEW`, que grava o evento): `RESULTADO: OK`, exit 0.

## Pronto para `CODE_REVIEW`?

- [x] Sim — `allowed_paths` respeitado, comandos acima com exit 0, decisões fora da spec declaradas
- [ ] Não — motivo:

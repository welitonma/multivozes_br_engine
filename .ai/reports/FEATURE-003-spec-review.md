# Spec Review — FEATURE-003

**Revisor:** spec-reviewer (sessão nova; não escreveu a spec)
**Data:** 2026-11-09
**Spec avaliada:** `.specs/features/CORRECOES/spec.md`
**Contract:** `.ai/tasks/FEATURE-003.json` (status `SPEC_REVIEW` confirmado; branch `fix/correcoes` confirmada; 9 `required_checks`)

## Veredito

- [x] Aprovada — segue para `READY_FOR_IMPLEMENTATION`
- [ ] Rejeitada — volta para `SPEC_DRAFT`

Motivo: os 6 bloqueantes da rodada 1 foram todos corrigidos na spec/contract e cada
correção foi **reproduzida com saída real de comando** (detalhes abaixo). Nenhum
bloqueante novo. Restam 3 sugestões não-bloqueantes para o worker/revisor de código.

## Rodadas

- **Rodada 1** (sessão anterior): rejeitada — 6 achados bloqueantes de redação/comando
  (subprocesso `-I`, AC3 `xfail` vs docstring, AC4 sem `--exclude-dir`, ruff sem o 5º
  erro de `tests/test_utils.py`, AC9/`__pycache__`, item 9 sem `tts-handler.md`/AC8 vago)
  + 6 sugestões. Relatório anterior preservado no histórico; esta rodada re-verifica
  cada ponto contra a spec reescrita.
- **Rodada 2** (esta): todos os 6 bloqueantes conferidos como corrigidos, com prova
  executada em cópias sob `.ai/tmp/` (originais e `tests/` intactos). Rodada 2 de no
  máximo 3. Veredito: **aprovada**.

## Método (provas executadas, sem tocar código/tests originais)

- Baseline original intacto: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` →
  **55 passed, 5 xfailed**; `--collect-only -q | grep -c '::'` → **60**.
- Cópias em `.ai/tmp/r2` (patch do item 6), `.ai/tmp/r2b` (decoradores xfail removidos),
  `.ai/tmp/r2c`+`.ai/tmp/r2d` (patch do item 7), `.ai/tmp/r2e` (patch B1). Cópias de
  sessões anteriores em `.ai/tmp/` reaproveitadas só como prova de ruído (achado 3).
- Cada `required_check` do contract foi rodado **literalmente** no estado atual para
  provar o caso negativo (exit codes registrados). Nenhum `.env` lido/criado
  (`test ! -e .env` ok); sem rede; sem servidor; sem `rm -rf` (bloqueado pelo guarda).

## Pontos levantados

| # | Severidade (bloqueante/sugestão) | Descrição |
| - | --------------------------------- | --------- |
| 1 | bloqueante (rodada 1) — **corrigido** | Item 8/AC6: spec agora manda **sem `-I`** (`sys.path.insert(0, RAIZ)`, RAIZ de `__file__`) com env mínimo explícito. Reproduzido em cópia: `PORT=abc/0/70000`, `DEFAULT_SPEED=abc/9`, `DEFAULT_RESPONSE_FORMAT=xyz` → exit 1 + trecho literal; valores válidos (`PORT=1/5050/65535`, `DEFAULT_SPEED=0.25/1.0/2.0`) passam. Negativo provado no original: `PORT=abc` dá `ValueError: invalid literal` (cita `PORT` na linha do `getenv`, mas **não** o trecho); `PORT=0` e `DEFAULT_SPEED=9` aceitos silenciosamente (rc=0). |
| 2 | bloqueante (rodada 1) — **corrigido** | AC3 agora é `grep -rn "xfail(" tests/` (com parêntese), igual ao check do contract. Reproduzido: removidos os 5 decoradores em cópia → grep vazio; a docstring `tests/test_api.py:1` ("como xfail estrito", sem parêntese) não atrapalha. |
| 3 | bloqueante (rodada 1) — **corrigido** | AC4 agora tem `--exclude-dir=.venv --exclude-dir=.ai --exclude-dir=.specs --exclude-dir=.estrutura --exclude-dir=.git`. Literal no estado atual acha só os 3 hits reais (`.env.example:33,47`, `config.py:10`); sem `--exclude-dir`, `.ai/tmp/*/config.py` de outras sessões poluem (provado: 4+ cópias). Pós-patch o comando dá vazio por construção. |
| 4 | bloqueante (rodada 1) — **corrigido** | Item 7 agora lista as **5 ocorrências** (inclui `import os` sem uso em `tests/test_utils.py:3`, F401). `ruff check --select E9,F --no-cache --isolated .` hoje = 5 erros (4 em `main.py` + 1 em `tests/test_utils.py`); cópia com os 5 pontos + `ignore` removido → `All checks passed!` no modo isolated **e** no `ruff check .` normal. |
| 5 | bloqueante (rodada 1) — **corrigido** | AC1 agora fixa `PYTHONDONTWRITEBYTECODE=1` nos dois comandos pytest e contagem `grep -c '::'` ≥ 60 (hoje exatamente 60 = 55+5; item 8 **acrescenta** testes → alvo realista e crescente). AC9 agora tem comando próprio (`find ... -not -path ...` → vazio) + `test ! -e .env` (ok hoje) + instrução de `PYTHONDONTWRITEBYTECODE=1` em todo comando Python. Observação: `./__pycache__` **já existe** hoje (gitignorado) — o worker precisa removê-lo (ver sugestão S2). |
| 6 | bloqueante (rodada 1) — **corrigido** | Item 9 agora cita `tts-handler.md` l.28-29 e l.121-122 (conferidas em disco: afirmam `2.0 < speed <= 4.0 → 500`, falsas pós-B2). AC8 agora é concreto: dois `git grep` + regra de revisão manual ("nenhum resíduo pode afirmar que B1–B4 seguem abertos; 'corrigido na Fase 2' permitido"). O resíduo do 2º grep é grande (menções legítimas a 403/smoke tests/`lacuna`/`sem uso`), mas a regra o torna **possível** — cabe ao revisor de código, não ao exit code. |
| 7 | sugestão (rodada 1) — **atendido** | B1 agora fixa a ordem (`CHAVE_API` ausente → 500 **primeiro**, mesmo sem cabeçalho) e `WWW-Authenticate: Bearer` **nos dois** 401. Implementado em cópia e provado com TestClient: sem-cabeçalho → 401+header; `Basic` → 401+header; Bearer errada → 401+header; sem `CHAVE_API` + sem cabeçalho → 500; `REQUIRE_API_KEY=false` sem cabeçalho → passa (200). |
| 8 | sugestão (rodada 1) — **atendido** | Item 6 agora crava: validação em `main.py:34-37`, sem helper em `utils.py`; `RuntimeError` (stderr) com prefixo exato `Configuração inválida: NOME='valor'`; AC6 procura em stdout+stderr. |
| 9 | sugestão (rodada 1) — **atendido** | Item 8 declara que a mensagem 422 é a do Pydantic (inglês) e o teste confere status + campo `speed`. Sem ida-e-volta. |
| 10 | sugestão (rodada 1) — **atendido** | Item 8: ausência de `DEFAULT_LANGUAGE`/`EXPAND_API` testada lendo **somente** `config.py` + `.env.example` (escopo fechado, sem varredura de árvore no teste). |
| 11 | sugestão (rodada 1) — **atendido** | Contract agora tem os checks que faltavam: collect `≥ 60` e AC6 do `PORT=abc` (9 checks no total). |
| 12 | sugestão (rodada 1) — **atendido** | Item 8 usa env mínimo explícito (`PATH`, `PYTHONDONTWRITEBYTECODE=1`, `REQUIRE_API_KEY=false`, `API_KEY=teste` + a variável do caso); como `load_dotenv` não sobrescreve variável definida e AC9 proíbe `.env`, não há vazamento nas variáveis fixadas. |
| S1 | sugestão (nova, não-bloqueante) | AC2: `grep -nE "ignore|F401|F541" pyproject.toml` também casa as strings `F401`/`F541` — o worker **não** deve deixar essas strings nem em comentários novos (apagar o bloco `ignore` inteiro basta; `select = ["E9","F"]` e `extend-exclude` passam limpos, provado). |
| S2 | sugestão (nova, não-bloqueante) | AC9: `./__pycache__` pré-existe (gitignorado, com `main`/`config`/`handle_text` `.pyc`). O worker deve removê-lo ao final sem `rm -rf` (ex.: `.venv/bin/python -c` com `shutil`) e manter `PYTHONDONTWRITEBYTECODE=1` em tudo. Verificação do revisor de código. |
| S3 | sugestão (nova, não-bloqueante) | Item 4: "registrá-lo em teste de caracterização, **se ainda não existir**" (texto que só esvazia pós-filtro, ex. só emoji) — cabe ao revisor de código conferir a existência/cobertura. |

## Detalhes e evidências

**1. AC6 literal, sem patch (original):**
`out=$(PORT=abc PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c "import sys; sys.path.insert(0, '.'); import main" 2>&1); rc=$?` →
`rc=1`, `ValueError: invalid literal for int() with base 10: 'abc'`, `grep -q "Configuração inválida: PORT='abc'"` **falha** (caso negativo do check confirmado, `rc=1` no check exato do contract).
`DEFAULT_SPEED=9` e `PORT=0` sem patch → `rc=0` (aceitos silenciosamente — o check falha também por `test $rc -ne 0`).

**1b. Com patch do item 6 (cópia `.ai/tmp/r2`):** os 6 casos inválidos → `rc=1` + trecho
literal (`PORT='abc'/'0'/'70000'`, `DEFAULT_SPEED='abc'/'9'`, `DEFAULT_RESPONSE_FORMAT='xyz'`);
válidos (`PORT=1/5050/65535`, `DEFAULT_SPEED=0.25/1.0/2.0`) → `rc=0` + `OK`.

**2. AC3:** original tem 5 `xfail(` (linhas 88/95/105/113/121 de `tests/test_api.py`) + docstring
da linha 1 sem parêntese. Cópia `.ai/tmp/r2b` sem os decoradores: `grep -rn "xfail("` → vazio.

**3. AC4:** literal hoje → 3 hits (`./.env.example:33`, `./.env.example:47`, `./config.py:10`);
`.ai/tmp/ac7-{vel,link,voz}/config.py`, `ac8-rede`, `rev-mut1` provam o ruído excluído.

**4. Ruff:** `ruff check --select E9,F --no-cache --isolated .` → 5 erros
(`main.py:2` F401, `main.py:115/116/117` F541, `tests/test_utils.py:3` F401 `os`).
Cópia `.ai/tmp/r2d` com as 5 correções e sem `ignore` → `All checks passed!` (isolated e normal).
Nota: o isolated geral respeita `.gitignore` (`.ai/tmp` com 83 erros próprios é ignorado;
`--no-respect-gitignore` daria 88) — o AC2 é estável.

**5. AC1/AC9:** collect → `60`, `grep -c` exit 0; `test ! -e .env` ok; `find` hoje lista
`./__pycache__` (ver S2). `pytest -q` com a var não recria cache.

**6. AC8:** 1º `git grep` hoje → 9 hits (`.env.example`, `config.py`, `README.md:70-71/91/93`,
`deploy.md:90/93`, `texto-config-utils.md:53`) — todos no escopo do item 9, zeráveis.
2º grep → ~20 hits (fluxo auth, tabelas 400/**403**/500, smoke tests 403, `sem uso`/`lacunas`)
— resíduo legítimo sob a regra de revisão manual.

**7. B1 (cópia `.ai/tmp/r2e`, TestClient):** sem cabeçalho `401 + Bearer`; `Basic abc`
`401 + Bearer`; Bearer errada `401 + Bearer`; `CHAVE_API=None` + sem cabeçalho `500`;
`REQUIRE_API_KEY=false` sem cabeçalho `200` (passa). Ordem e headers conformes.

**8. `required_checks` exatos no estado atual (exit codes):** vars-mortas `1` (acha
`config.py` primeiro) ✓negativo; `ignore` `1` ✓negativo; `xfail(` `1` ✓negativo;
AC6 `1` ✓negativo; pycache `1` (só pelo `__pycache__` pré-existente) ; `pytest` `0`;
`ruff` `0`; `git status` 4 arquivos `0`; collect `0`. Pós-patch hipotético: os 4 negativos
viram `0` (provado por 1b/2/3/4), os demais seguem `0` — bateria coerente e capaz de
detectar regressão em ambas as direções.

**9. Coerência geral:** item 2 preserva a ordem atual do código (`EXIGIR → CHAVE_API → credentials`);
B1 `Basic`-errado→401 decorre do `HTTPBearer(auto_error=False)` (None p/ esquema errado,
confirmado via TestClient); item 8 cobre `speed=2.0/0.25` aceitos e `2.01/0.24 → 422`
(Pydantic `ge/le`, trivial); AC5 mutação é o inverso da prova XPASS da rodada 1;
AC7 excepciona artefatos do protocolo; `test_texto_vazio_comportamento_real` (500→400) e
aperto `(401,403)`→401 seguem previstos no item 8. Nenhuma ambiguidade nova relevante
além de S1–S3.

## Escopo confirmado

- `allowed_paths` da task contract cobre o necessário? **Sim** — `main.py`, `config.py`,
  `.env.example`, `pyproject.toml`, `tests/**`, `docs/aplicacao/**`,
  `docs/desenvolvimento.md` cobrem todos os itens 1–9; `utils.py`/`tts_handler.py`
  corretamente fora (item 6 veda helper em `utils.py`; `velocidade_para_taxa` inalterada).
- `required_checks` fazem sentido pro que a spec pede? **Sim** — os 9 checks cobrem
  AC1 (pytest + collect ≥ 60), AC2 (ruff + grep de `ignore`), AC3 (`xfail(`), AC4/AC8-1ª
  parte (loop de variáveis mortas), AC6 (subprocesso `PORT=abc`), AC7 (git status dos 4
  arquivos) e AC9 (find `__pycache__`); cada um passa no final hipotético e falha hoje
  quando deve (casos negativos provados acima).

## Observações adicionais

- Transição aplicada por este revisor: tentativa de `SPEC_REVIEW → READY_FOR_IMPLEMENTATION` **bloqueada pelo gate** (`rc=1`: "exige decisao humana explicita (--human) porque human_approval_required=true"). Conforme o brief, este revisor **não** usou `--human`: a aplicação fica pendente para o humano (`node .estrutura/ai-protocol/gates/validate-task-state.mjs FEATURE-003 READY_FOR_IMPLEMENTATION --human --actor=humano` ou equivalente). Task permanece em `SPEC_REVIEW` até lá; o veredito desta revisão é **aprovada**.
- Temporários desta rodada em `.ai/tmp/r2`, `.ai/tmp/r2b`, `.ai/tmp/r2c`, `.ai/tmp/r2d`,
  `.ai/tmp/r2e` (gitignorados; originais e `tests/` intactos — `git status` só mostra
  artefatos do protocolo + `.ai/events.jsonl` já modificado antes da sessão).

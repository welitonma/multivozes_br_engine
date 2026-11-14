# Code Review — FEATURE-003

**Revisor:** code-reviewer (sessão independente; não implementou nada)
**Data:** 2026-11-14
**Branch:** `fix/correcoes` (mudanças do worker NÃO commitadas — `git status/diff`)
**Status do contract confirmado:** `CODE_REVIEW`

> Regra fixa: revisor nunca corrige, só reporta.

## Veredito

- [ ] Aprovado — segue para `TESTING`
- [x] Mudanças pedidas — volta para `FIXING`

Motivo: o código (B1–B4, variáveis mortas, validação de configuração, testes,
ruff) foi todo reproduzido e está correto. O único bloqueio é documental:
`main.py` cresceu ~24 linhas e **~20 referências de linha em 4 arquivos de
docs continuam apontando para as linhas antigas** (o brief desta revisão exigia
explicitamente essa conferência). Correção trivial, toda dentro de
`allowed_paths` (`docs/aplicacao/**`).

## Findings

| # | Arquivo:linha | Severidade | Descrição | Reprodução |
| - | -------------- | ---------- | --------- | ---------- |
| 1 | `docs/aplicacao/main.md:12` | média | `text_to_speech` citado como `main.py:66-99`; o símbolo real é `main.py:89-122` (def em 89, `FileResponse` em 115, fim do `except` em 122). | `grep -n "def text_to_speech\|FileResponse\|except HTTPException" main.py` → 89, 115, 117 |
| 2 | `docs/aplicacao/main.md:18` | média | 400 do `input` citado como `main.py:71-73`; real `main.py:95-97`. | `sed -n 95,97p main.py` |
| 3 | `docs/aplicacao/main.md:23` | baixa | `VOZ_PADRAO` citada como `main.py:81`; real `main.py:41`. | `grep -n "VOZ_PADRAO =" main.py` |
| 4 | `docs/aplicacao/main.md:35,37,41,43,45` | média | Fluxo interno cita `main.py:75-77` (filtro), `main.py:81-85` (MIME), `main.py:88` (`gerar_audio`), `main.py:91` (`unlink`), `main.py:93` (`FileResponse`); reais `100-101`, `104-107`, `110`, `113`, `115`. | `sed -n 99,115p main.py` |
| 5 | `docs/aplicacao/main.md:47` | baixa | `listar_modelos` citada como `main.py:102-108`; real `main.py:126-131`. | `grep -n "def listar_modelos" main.py` |
| 6 | `docs/aplicacao/main.md:80,84,104,108` | baixa | Config lida "em `main.py:34-38`", `uvicorn` em `main.py:122`, banner em `main.py:111-122`; reais bloco `34-52`, `uvicorn.run` em `146`, banner `135-146`. Corretas e mantidas: `21-28`, `:28`, `:31`, `1-16`. | `grep -n "uvicorn.run\|__main__\|_PORT_BRUTO\|REMOVER_FILTRO =" main.py` |
| 7 | `docs/aplicacao/texto-config-utils.md:9,42,48,50-54` | média | `main.py:77` (filtro) → real 101; `main.py:34-38` → real 34-52; tabela: `PORT :34` (ok parcial — `_PORT_BRUTO`; `PORTA` em 36/39-40), `DEFAULT_VOICE :35` → 41, `DEFAULT_RESPONSE_FORMAT :36` → 42, `DEFAULT_SPEED :37` → 45/47, `REMOVE_FILTER :38` → 52. | mesmos comandos acima |
| 8 | `docs/aplicacao/tts-handler.md:8,69` | baixa | `main.py:88` → real 110; `main.py:91` → real 113. (As correções de conteúdo das l.28-29 e 121-122 estão certas: faixa `0.25–2.0` e 422.) | `grep -n "gerar_audio(texto\|os.unlink" main.py` |
| 9 | `docs/aplicacao/deploy.md:90,92-93` | baixa | Tabela: `REMOVE_FILTER` em `.env.example:40` (real 36), `DETAILED_ERROR_LOGGING` em `:44` (real 40), `PROXY` em `:51-52` (real 43). Ficaram obsoletas como efeito colateral da remoção dos blocos `DEFAULT_LANGUAGE`/`EXPAND_API` (linhas corretas antes: `PORT :4`, `API_KEY :12`, `REQUIRE :16`, `VOICE :23`, `FORMAT :26`, `SPEED :29`, `config.py` — todas ainda OK). | `grep -n "PORT=\|API_KEY=\|REQUIRE\|VOICE=\|FORMAT=\|SPEED=\|REMOVE_FILTER=\|DETAILED\|PROXY" .env.example` |
| 10 | (info, sem ação obrigatória) | info | `grep` literal do AC4 da spec (`--include='*.py'`) casa `tests/test_api.py:215,219` — mas essas são as *strings do próprio teste* que prova a ausência (`for morta in (...)`). O `required_check` do contract (loop nos 6 arquivos, sem `tests/`) passa vazio. Imprecisão de redação da spec, não defeito do worker. | `grep -rnE "DEFAULT_LANGUAGE\|EXPAND_API" --include='*.py' ...` → só `tests/test_api.py`; loop do contract → vazio |
| 11 | (info, sem ação obrigatória) | info | `docs/aplicacao/deploy.md` (Observações, linha pré-existente, worker não tocou): "a conversão de string para booleano vive em `config.py`" — na verdade vive em `utils.py:8-11` (`obter_env_bool`). Sugestão Fase 3, fora do escopo da Fase 2. | `grep -n "def obter_env_bool" utils.py` → 8 |

Nada nos findings 1–9 altera comportamento; o texto comportamental dos docs
(B1–B4 como "corrigido na Fase 2", tabelas PORT/DEFAULT_*, fluxo 401/422/500)
foi conferido e está correto.

## O que foi reproduzido (saída e exit code reais)

- `node .estrutura/ai-protocol/gates/check-gates.mjs FEATURE-003` → `RESULTADO: OK`, exit 0 (9 `required_checks` + artefatos + anti-silêncio).
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` → `74 passed`, 0 failed/0 xfailed/0 xpassed; collect `74` (≥ 60). `.venv/bin/ruff check .` e `--select E9,F --no-cache --isolated` → `All checks passed!`.
- **B1** (`.ai/tmp/review-ataque.py`, TestClient, sem rede/servidor): matriz completa — OFF sem-cabeçalho→200, OFF Bearer errada→200; ON sem-cabeçalho/Basic/Bearer errada→401 com `www-authenticate: Bearer`; ON Bearer certa→200; CHAVE ausente (`None` e `""`) com/sem cabeçalho/Basic→500 (ordem da spec respeitada). `bearer` minúsculo com segredo certo→200: correto (esquema RFC 7235 é case-insensitive; o `HTTPBearer` só devolve `None` para esquema *diferente*). `/docs`, `/openapi.json`, `/v1/models` → 200 com checagem ligada. 1ª expectativa minha errada (`bearer` minúsculo), não bug.
- **B2/B3**: `0.25/2.0`→200; `2.01/0.24/3.0/4.0/"rapido"`→422 com `loc` em `speed`; omitido/`null`→200; `"1.5"` coagido→200 (Pydantic, ok). Padrões `VELOCIDADE_PADRAO=1.5`/`FORMATO=wav` aplicados quando omitidos; cliente (`speed 1.0`/`mp3`) sempre vence; `FileResponse` sai `speech.wav` no padrão e `speech.mp3` no override; `response_format` desconhecido→200 `audio/mpeg` (comportamento pré-existente mantido).
- **B4**: `input ""`→400 `{"detail":"O campo 'input' é obrigatório."}`; erro genuíno de síntese (`RuntimeError: edge caiu`)→500 com detalhe; 422 de `speed` intacto (não vira 500 — `except HTTPException: raise` ok); só-emoji→200 com `gerar_audio` chamado com `''` (caracterização correta).
- **Configuração** (subprocesso `env -i`, 1 caso por processo): `PORT=abc/0/70000/-1/""/"5050.0"/65536`→rc=1 + `Configuração inválida: PORT='<v>'`; `PORT=1/65535/" 8080 "`→rc=0 (`int()` aparar espaço é semântica Python, aceitável). `DEFAULT_SPEED=abc/9/0/nan/inf/-inf/0.24/2.01/""`→rc=1 (`nan`/`inf` rejeitados corretamente: comparação com `nan` é falsa e `inf` sai da faixa). `DEFAULT_SPEED=1.5/0.25/2.0/" 1.5 "`→rc=0. `DEFAULT_RESPONSE_FORMAT=xyz/MP3/WAV/""/" mp3"`→rc=1 (chaves exatas de `TIPOS_MIME_AUDIO`, conforme a spec); `mp3/wav/opus`→rc=0. Variáveis ausentes→rc=0 com defaults `5050/1.0/mp3` (defaults do `config.py` continuam valendo).
- **Variáveis mortas**: loop do contract vazio; `config.py`/`.env.example` sem sobras (sem comentários órfãos nem linhas em branco duplicadas — `.env.example` íntegro); primeiro grep do AC8 vazio; segundo grep com 4 resíduos, todos históricos/legítimos (`README:73` título + itens 1–4/14 riscados "corrigido na Fase 2"; `docs-existentes.md:141` changelog/`voices.example.json` = Fase 3; `main.md:75` cita `403/401` **do comportamento antigo, marcado "(corrigido na Fase 2: antes, …)"** — permitido).
- **Qualidade dos testes (mutação em cópia integral em `.ai/tmp/mut-b*`, originais intactos)**: `HTTPBearer()`→4 failed; `le=4.0`→2 failed; ignorar padrões→9 failed; sem `except HTTPException: raise`→2 failed; sem validação de PORT→3 failed. Cada reversão derruba ≥2 testes (sem o artefato `FileNotFoundError` do harness mínimo do worker). Testes de subprocesso usam `env -i` explícito (`PATH`, `PYTHONDONTWRITEBYTECODE=1`, `REQUIRE_API_KEY=false`, `API_KEY=teste` + caso) e a rede é bloqueada pelo `socket.connect` no `conftest.py`; nenhum teste lê `.env` (`test ! -e .env` ok). Zero `xfail(`; `pyproject.toml` sem `ignore`/`F401`/`F541`.
- **Escopo**: `git diff --name-only` só `allowed_paths` + `.ai/events.jsonl` (artefato do protocolo); `Dockerfile`, `requirements*.txt`, `voices.json`, `utils.py`, `tts_handler.py`, `handle_text.py` intactos; sem `__pycache__` (fora `.venv/.estrutura/.ai/tmp`) e sem `.env`. Português do Brasil nos docs tocados.

## Checagens de escopo

- Mudanças ficaram dentro de `allowed_paths`? Sim — `main.py`, `config.py`, `.env.example`, `pyproject.toml`, `tests/**`, `docs/aplicacao/**`, `docs/desenvolvimento.md` (+ `.ai/events.jsonl`, artefato do protocolo).
- Algum arquivo sensível tocado (.env, credentials, etc.)? Não — `test ! -e .env` (exit 0); nenhum `.env` lido ou criado; sem rede (conftest bloqueia `socket.connect`; coverage `-p no:cacheprovider` nas cópias).

## Checagens de segurança (bloqueante se SIM)

- [ ] Segredos/credenciais expostos (token, senha, connection string, chave)? Não — `API_KEY` do `.env.example` é placeholder; testes usam `API_KEY=teste` em env isolado.
- [ ] Injeção possível (comando shell, path traversal, XSS)? Não — `os.unlink` em caminho gerado pelo próprio app; `int()`/`float()` sem `eval`.
- [ ] Falha de autorização/controle de acesso (rota/função sem checar permissão)? Não — B1 verificado na matriz; `/v1/models` aberta é decisão registrada da spec (HEALTHCHECK).
- [ ] Dependência nova ou script de install sem revisão (RCE/supply-chain)? Não — zero dependências novas; `.venv` só usado para `pytest`/`ruff`/`python`.
- [ ] Log/erro vaza dado sensível? Não — detalhe 500 expõe só `str(e)` de síntese; `CHAVE_API` nunca entra em mensagem (validação de config ecoa só `PORT`/`DEFAULT_*`, sem segredo).

## Para o worker (FIXING, escopo fechado)

Atualizar apenas os números de linha dos findings 1–9 (mapa real medido:
`text_to_speech` 89–122; 400 em 95–97; `VOZ_PADRAO` 41; filtro 100–101; MIME
104–107; `gerar_audio` 110; `unlink` 113; `FileResponse` 115; `listar_modelos`
126–131; bloco config 34–52; `uvicorn.run` 146; banner 135–146; `.env.example`
`REMOVE_FILTER` 36, `DETAILED_ERROR_LOGGING` 40, `PROXY` 43). Nenhuma mudança
de código. Re-rodar `check-gates.mjs` após o retoque.

---

# Rodada 2 — 2026-11-14 (revisor independente; não implementou nada)

**Status do contract confirmado:** `CODE_REVIEW` | **Branch:** `fix/correcoes` (mudanças NÃO commitadas)

## Veredito da rodada 2

- [x] Aprovado — segue para `TESTING`
- [ ] Mudanças pedidas — volta para `FIXING`

O ciclo de correção 1 resolveu os findings 1–9 sem tocar em código nem testes.
Nada mais bloqueia.

## 1. Findings 1–9: todas as referências conferem (nenhuma errada)

Conferência: `grep -rn "main.py:" docs/` + `grep -rn ".env.example:" docs/`
contra `grep -n`/`sed -n` no `main.py` e `.env.example` reais.

- `docs/aplicacao/main.md:12` `89-122` ✓ (def 89, `FileResponse` 115, fim do `except` 122); `:18` `95-97` ✓; `:23` `VOZ_PADRAO :41` ✓; `:35,37,41,43,45` `100-101` ✓ / `104-107` ✓ / `:110` ✓ / `:113` ✓ / `:115` ✓; `:61` `listar_modelos 126-131` ✓ (decorator 126 → return 131); `:87` bloco config `34-52` ✓ (`_PORT_BRUTO` 34, `PORTA=int` 36, faixa 39-40, `FORMATO_RESPOSTA_PADRAO` 42, `_VELOCIDADE_BRUTA` 45, `VELOCIDADE_PADRAO` 47, `REMOVER_FILTRO` 52); `:100,103,113` imports `1-16` ✓, `uvicorn.run :146` ✓, banner `135-146` ✓ (`if __name__` 135 → `uvicorn.run` 146).
- `docs/aplicacao/texto-config-utils.md` `:9` `100-101` ✓; `:42` `34-52` ✓; tabela `PORT :36,39-40` ✓, `DEFAULT_VOICE :41` ✓, `DEFAULT_RESPONSE_FORMAT :42` ✓, `DEFAULT_SPEED :45,47` ✓, `REMOVE_FILTER :52` ✓.
- `docs/aplicacao/tts-handler.md:8` `:110` ✓; `:69` `:113` ✓.
- `docs/aplicacao/deploy.md:90-92` `REMOVE_FILTER :36` ✓, `DETAILED_ERROR_LOGGING :40` ✓, `PROXY :43` (linha única comentada) ✓; demais linhas da tabela (`PORT :4`, `API_KEY :12`, `REQUIRE :16`, `VOICE :23`, `FORMAT :26`, `SPEED :29`) continuam OK.
- `docs/aplicacao/README.md` e `docs/desenvolvimento.md`: zero ocorrências de `main.py:` / `.env.example:` — nada a corrigir.

## 2. Código e testes intactos no ciclo (só docs mudaram)

- Sinais do código aprovado na rodada 1 presentes e inalterados: `HTTPBearer(auto_error=False)` (`main.py:18`), `le=2.0` (`main.py:27`), `except HTTPException: raise` (`main.py:117`), prefixo `Configuração inválida: NOME='valor'` (linhas 38/40/44/49/51).
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` → `74 passed`, 0 failed/0 xfailed/0 xpassed, exit 0 (re-rodado nesta rodada). Collect `74` (≥ 60). `.venv/bin/ruff check .` → `All checks passed!`, exit 0.
- `grep -rn 'xfail(' tests/` → vazio.

## 3. Gates, escopo e higiene

- `node .estrutura/ai-protocol/gates/check-gates.mjs FEATURE-003` → `RESULTADO: OK`, exit 0 (9 `required_checks` + artefatos + anti-silêncio).
- `git diff --name-only`: só `allowed_paths` (`main.py`, `config.py`, `.env.example`, `pyproject.toml`, `tests/**`, `docs/aplicacao/**`, `docs/desenvolvimento.md`) + `.ai/events.jsonl` (artefato do protocolo, permitido pelo AC7). `Dockerfile`, `requirements*.txt`, `voices.json` intactos. Nenhum arquivo sensível tocado; `test ! -e .env` OK (não lido nem criado; sem rede; sem servidor).
- `find . -name __pycache__ -not -path './.venv/*' -not -path './.estrutura/*' -not -path './.ai/tmp/*'` → vazio.

## 4. Itens info da rodada 1: seguem sem ação obrigatória

- Info 10 (AC4): `grep --include='*.py'` casa só `tests/test_api.py:215,219` — as strings do próprio teste que prova a ausência; o loop do contract (6 arquivos, sem `tests/`) sai vazio. Redação da spec, não defeito.
- Info 11 (`deploy.md:100` "conversão ... vive em `config.py"`): linha pré-existente, intocada pelo ciclo (`git diff -- docs/aplicacao/deploy.md` só mostra as linhas da tabela 90-92); a função vive em `utils.py:8`. Sugestão Fase 3, fora do escopo.

## Checagens de segurança (rodada 2 — bloqueante se SIM)

- [ ] Segredos expostos? Não — nada novo; `.env.example` só placeholder.
- [ ] Injeção possível? Não — ciclo só alterou texto de docs.
- [ ] Falha de autorização? Não — B1 inalterado e revalidado via suíte (74 passed).
- [ ] Dependência nova? Não.
- [ ] Log vaza sensível? Não.

Transição executada: `validate-task-state.mjs FEATURE-003 TESTING --actor=code-reviewer`.

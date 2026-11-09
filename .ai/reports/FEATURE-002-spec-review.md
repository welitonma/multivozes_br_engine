# Spec Review — FEATURE-002

**Revisor:** spec-reviewer (sessão independente; não escreveu a spec)
**Data:** 2026-11-06 (rodada 2)
**Spec avaliada:** `.specs/features/TESTES/spec.md`
**Contract:** `.ai/tasks/FEATURE-002.json` (status inicial confirmado: `SPEC_REVIEW`)
**Branch:** `feat/testes` — ambiente `.venv` existente; todos os comandos com `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python` e scripts em `.ai/tmp/` (nada em `tests/`, nenhum `.py` alterado, sem rede, sem `.env` lido/criado, sem commit/push)

## Veredito

- [x] Aprovada — segue para `READY_FOR_IMPLEMENTATION`
- [ ] Rejeitada — volta para `SPEC_DRAFT`

Rodada 2 de no máximo 3. O único ponto bloqueante da rodada 1 (B2) foi corrigido na spec e REPRODUZIDO aqui: o falso que chama `tts_handler.velocidade_para_taxa` devolve 500 para `speed=3.0`, como a spec agora afirma. Nenhum bloqueante restante.

## Método

Cada afirmação da spec sobre o código foi medida com saída real de comando (script `.ai/tmp/spec002_rodada2.py`; checagens pontuais via `grep`/`git check-ignore`/`ruff`). Resumo do medido:

| Medição | Resultado |
|---|---|
| B2 com o falso **como a spec agora descreve** (chama `velocidade_para_taxa` antes de gravar) + `speed=3.0` | **500** `{"detail":"Erro interno no servidor: A velocidade deve estar entre 0.25 e 2.0."}` → texto de B2 **procede** |
| B2 com falso simples (sem o passo 2) + `speed=3.0` | **200** → confirma o diagnóstico da rodada 1 (sem o passo 2 o B2 seria invisível); a spec agora exige o passo (2), ambiguidade eliminada |
| B4: `input: ""` + falso + `REQUIRE_API_KEY=false` + Authorization qualquer | **500** `{"detail":"Erro interno no servidor: 400: O campo 'input' é obrigatório."}` → hipótese B4 **procede**, entra sempre |
| B1: `REQUIRE_API_KEY=false` sem cabeçalho | **403** `{"detail":"Not authenticated"}` → xfail correto |
| B3: `VELOCIDADE_PADRAO=1.5` + `FORMATO_RESPOSTA_PADRAO="wav"`, requisição sem `speed`/`response_format` | `gerar_audio` recebeu `(..., 'mp3', 1.0)`, `content-type: audio/mpeg` → **ignorados, xfail correto** |
| Auth `EXIGIR=True`: certa→200, errada→401, sem cabeçalho→403, `CHAVE_API=None`→500 | conforme a spec; regra "401 ou 403" justificada (403 vem do `HTTPBearer(auto_error)` antes da dependência) |
| `GET /v1/models` sem cabeçalho | 200 com `tts-1` e `tts-1-hd` |
| Fixture `socket.socket.connect` bloqueado + TestClient | todos os POST/GET acima rodaram com `connect` bloqueado → **compatível** (ASGITransport não usa socket) |
| `asyncio.run` + `gerar_audio_normal`/`gerar_audio_com_pausas` | ambos existem e são corrotinas (`iscoroutinefunction` True); `gerar_audio` é `async` |
| Config na importação | trocar `os.environ` depois do `import main` **não** muda `main.EXIGIR_CHAVE_API` → `monkeypatch.setattr(main, …)` necessário, como a spec diz |
| `load_dotenv` | não sobrescreve env existente (provado: `REQUIRE_API_KEY=true API_KEY=zzz` exportados sobrevivem ao `load_dotenv` e chegam a `main`) |
| `main.py:74-75` e `95-99` | `if not texto:` está na linha **74** (raise na 75); `except Exception` na linha **95** → refs da spec **conferem** |
| `main.py:34-38` e `36-37` | `VOZ_PADRAO=35`, `FORMATO_RESPOSTA_PADRAO=36`, `VELOCIDADE_PADRAO=37`, `REMOVER_FILTRO=38` → conferem |
| `docs/desenvolvimento.md` linha 30 | `.venv/bin/pytest  # testes (testpaths = ["tests"]; os testes chegam na Fase 1)` → citação da spec **confere** |
| `sys.path` por `__file__` | spec agora exige `Path(__file__).resolve().parent.parent`, nunca absoluto → exigência da rodada 1 atendida |
| `ruff check .` hoje | exit 0 **com** aviso de depreciação (`grep -ci deprecated` = 1) → item 8 procede; migração `[tool.ruff.lint]` escrita à mão dá exit 0 e count **0** → factível (atenção: só `select`/`ignore` mudam de seção; `extend-exclude` fica em `[tool.ruff]`) |
| `.gitignore` hoje | só `.env`; `.env.local`/`.env.production` **não** ignorados → item 7 procede; padrão `.env.*` + `!.env.example` testado via `core.excludesFile`: `.env.local` ignorado, `.env.example` NÃO ignorado → factível |
| Loop `check-ignore` do contract (caso negativo) | hoje falha com `NAO ignorado: .env.local` + `NAO ignorado: .env.production` (exit 1) → o loop **consegue falhar**, não passa vazio |
| `git status --porcelain -- '*.py' ':!tests'` | vazio hoje; com `app.py` estranho em scratch lista `?? app.py` (com `tests/` excluído) → consegue falhar |
| Caso-limite Fase 0 (ruff sumido → `grep -c` daria 0) | a ordem dos checks cobre: `.venv/bin/ruff check .` falharia primeiro (exit 127) |

## Pontos levantados

| # | Severidade (bloqueante/sugestão) | Descrição |
| - | --------------------------------- | --------- |
| 1 | sugestão — §2 item 8 (ruff) | A migração correta move **só** `select`/`ignore` para `[tool.ruff.lint]`; `extend-exclude` permanece em `[tool.ruff]` (mover tudo quebra o TOML — `extend-exclude` não é chave de `lint`). A spec diz "mover `select` e `ignore`", o que já está certo; fica o registro para o worker não mover o bloco inteiro. Não bloqueante. |
| 2 | sugestão — AC3 (2ª rodada com env exportado) | Mantida da rodada 1: a 2ª rodada precisa **exportar antes** do `pytest` (config lida na importação) — `monkeypatch` não prova nada aqui. O comando do AC3 já está correto; só reforçar no relatório do worker. Não bloqueante. |

## Escopo confirmado

- `allowed_paths` da task contract cobre o necessário? Sim — `tests/**` (conftest + 4 arquivos de teste), `pyproject.toml` (item 8), `.gitignore` (item 7), `docs/desenvolvimento.md` (item 9). Nenhum `.py` fora de `tests/` muda (§4 fora do escopo explícito).
- `required_checks` fazem sentido pro que a spec pede? Sim — mapeiam 1:1 (pytest→AC1, ruff→AC4, `grep -ci deprecated`→AC4 2ª parte, `git status`→AC5, loop `check-ignore`→AC6). Cada um **pode falhar** (provado acima com casos negativos).

## Observações adicionais

- Total de xfails: 4 (B1–B4); AC1 "≥ 4" coerente.
- `tests/` contém só `.gitkeep` (confere com §1); sem `.env` no repo (só `.env.example`).
- Higiene: medições em `.ai/tmp/spec002_rodada2.py` (+ scripts da rodada 1) e scratchs `scratch_ruff*`/`scratch_neg*` — todos sob `.ai/tmp/` (git-ignorado), nenhum check afetado (AC5 medido vazio com eles presentes). Remoção manual com `rm -rf` segue vedada pelo guard; ficam registrados aqui.

## Histórico de rodadas

- **Rodada 1 (2026-11-06):** rejeitada — 1 bloqueante: B2 afirmava "hoje 500" mas o falso que a spec impunha desviava o `ValueError` (medido 200 em vez de 500); a spec precisava decidir entre (a) falso chamar `velocidade_para_taxa` ou (b) reescrever B2. Sugestões: refs `main.py:71-73`→`74-75`, `sys.path` por `__file__`, citação exata de `docs/desenvolvimento.md:30`, nota sobre AC3.
- **Rodada 2 (2026-11-06, este relatório):** a spec adotou a opção (a) — falso chama `tts_handler.velocidade_para_taxa(velocidade)` antes de gravar — e incorporou as 4 sugestões (refs 74-75/95-99, `__file__`, linha 30, AC3 com export). Todas **reproduzidas e confirmadas** acima. **Aprovada.**

## Transição de estado (pendente — humano aplica)

Tentativa de `validate-task-state.mjs FEATURE-002 READY_FOR_IMPLEMENTATION --actor=spec-reviewer` em 2026-11-06: **exit 1** — o gate exige decisão humana explícita (`--human`) porque `human_approval_required=true` no contract. Conforme a instrução da task, o revisor NÃO usa `--human`: a transição fica para o humano aplicar (`node .estrutura/ai-protocol/gates/validate-task-state.mjs FEATURE-002 READY_FOR_IMPLEMENTATION --human --note="..."`). Veredito técnico desta revisão: **aprovada**; estado em disco permanece `SPEC_REVIEW` até o humano transicionar.

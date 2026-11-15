# Code Review — FEATURE-002

**Revisor:** code-reviewer (sessão independente; não implementou nada)
**Data:** 2026-11-06
**Branch:** `feat/testes` | **Status confirmado:** `CODE_REVIEW`
**Worktree:** `.` (mudanças NÃO commitadas, conforme a task)

> Regra fixa: revisor nunca corrige, só reporta.

## Veredito

- [x] Aprovado — segue para `TESTING`
- [ ] Mudanças pedidas — volta para `FIXING`

Nenhum finding bloqueante. As duas ressalvas do worker foram reproduzidas e são aceitáveis (ver §Observações).

## Método (reprodução independente, nada aceito por relato)

`check-gates.mjs` + todos os `required_checks` e AC1–AC9 re-executados com
`PYTHONDONTWRITEBYTECODE=1`, `.venv` existente, sem instalar nada, sem servidor,
sem ler/criar `.env`, sem rede. Mutações e correções hipotéticas em CÓPIAS sob
`.ai/tmp/rev-*` (original intacto; `git status --porcelain -- '*.py' ':!tests'` vazio antes e depois).

| Verificação | Comando | Exit | Resultado |
|---|---|---|---|
| gates | `node .estrutura/ai-protocol/gates/check-gates.mjs FEATURE-002` | 0 | `RESULTADO: OK` (pytest 55 passed/5 xfailed, ruff ok, demais checks ok) |
| AC1 | `.venv/bin/pytest -q` | 0 | `55 passed, 5 xfailed` — 0 failed, 0 error, 0 xpassed |
| AC2 | `.venv/bin/pytest -q -rx` | 0 | 5 XFAIL listados com motivo (B1, B2, B3×2, B4) |
| AC3a | `env -u REQUIRE_API_KEY -u API_KEY .venv/bin/pytest -q` | 0 | `55 passed, 5 xfailed` |
| AC3b | `export REQUIRE_API_KEY=true API_KEY=x` antes + `.venv/bin/pytest -q` | 0 | `55 passed, 5 xfailed` |
| AC4 | `.venv/bin/ruff check .` / `grep -ci deprecated` | 0 | `All checks passed!` / `0` |
| AC5 | `git status --porcelain -- '*.py' ':!tests'` | 0 | vazio |
| AC6 | loop `check-ignore` do contract + lista ampla | 0 | `.env`, `.env.local`, `.env.production` ignorados; `.env.example`, `tests/test_api.py`, `voices.json` NÃO ignorados |
| AC7 | mutações em `.ai/tmp/rev-mut*` + `pytest -q` na cópia | — | cada mutação derruba ≥1 teste (tabela abaixo) |
| AC8 | conftest da cópia `.ai/tmp/rev-ac8` com `gerar_audio` real | — | 4 testes falham com 500 (prova que a fixture bloqueia) |
| AC9 | `.venv/bin/pytest --collect-only -q \| tail -3` | 0 | `60 tests collected` (≥ 25) |

### AC7 — mutações próprias (cópias `.ai/tmp/rev-mut*`)

| Mutação | Efeito |
|---|---|
| `tts_handler.py`: `<= 2.0` → `<= 4.0` | `test_velocidade_para_taxa_invalidos[2.01]` falha (1 failed) |
| `main.py`: `!= CHAVE_API` → `== CHAVE_API` | `test_auth_chave_certa` e `test_auth_chave_errada` falham (2 failed) |
| `tts_handler.py`: roteamento de pausas → `if False` | 2 testes de pausa falham |
| `handle_text.py`: `emoji.replace_emoji` → identidade | `test_remove_emoji` falha |
| `utils.py`: `"wav": "audio/wav"` → `"audio/mpeg"` | `test_tipos_mime_audio` + `test_formato_wav` falham |

Nenhum teste passa por motivo errado nos pontos atacados: as asserções são
exatas (valores, `content-type`, corpo não vazio, arquivo apagado, tupla de
argumentos `(texto, voz, formato, velocidade)`).

### xfails B1–B4 (estritos, razão correta, bug certo)

- Todos com `strict=True` e `reason` citando `arquivo:linha` + `docs/aplicacao/README.md` (itens conferidos no README: B1 = item 14 das lacunas; demais refs `main.py:18/36-37/74-75/95-99`, `tts_handler.py:44-45` conferem com o código).
- **B1:** sem cabeçalho + `EXIGIR=False` → 403 hoje. Correção hipotética em cópia (`HTTPBearer(auto_error=False)` + trata `None`) → `XPASS(strict)` → suíte falha. Descreve o bug certo.
- **B2:** `speed=3.0` → 500 hoje (`{"detail":"Erro interno no servidor: A velocidade deve estar entre 0.25 e 2.0."}`), reproduzido; o `audio_falso` replica a chamada a `velocidade_para_taxa`, sem a qual o B2 seria invisível. Descreve o bug certo.
- **B3:** provado que a rota nunca referencia `VELOCIDADE_PADRAO`/`FORMATO_RESPOSTA_PADRAO` (`"VELOCIDADE_PADRAO" in src` = False); com `VELOCIDADE_PADRAO=1.5` o falso recebe `1.0`. A correção real exige mudar defaults do pydantic (trabalho da Fase 2); o xfail falha hoje como esperado. Descreve o bug certo.
- **B4:** `input:""` → 500 hoje, reproduzido. Correção hipotética (checar antes do `try`) → `XPASS(strict)` + o teste de caracterização quebra (esperado por desenho: a Fase 2 atualiza a asserção de 500→400). Descreve o bug certo.

### Isolamento e ordem

- `conftest.py` força env via `os.environ[...] =` antes de qualquer import; `sys.path` derivado de `__file__`; fixture autouse bloqueia `socket.socket.connect` com `AssertionError`.
- AC8 em cópia: `gerar_audio` real → 4 testes falham com `500 == 200`; causa-raiz reproduzida diretamente: `RuntimeError: Falha ao gerar ou converter áudio: list index out of range` (o `AssertionError` é engolido pelo `aiohappyeyeballs`). Nenhuma chamada real ao `edge-tts` sai à rede.
- Arquivos de teste passam isolados (`test_api.py` 9+5 xfail; demais 13/13/20) e em ordem explícita alternativa; sem estado compartilhado (`monkeypatch` reverte tudo). (Nota honesta: flags `--reverse`/`randomly` não existem neste ambiente — pytest sem plugins de ordem; a independência foi evidenciada pelas rodadas isoladas.)
- Escrita: testes só criam `.mp3` via `tempfile` (conforme a spec §2 item 1) e o app apaga após a resposta (assert de exclusão no teste); meus temporários só em `.ai/tmp/rev-*`. Nenhum `.env` lido/criado (só `.env.example` existe). `__pycache__/` da raiz é git-ignorado e não commitado.
- Sem dependência nova (`asyncio.run`, sem `pytest-asyncio`); rede bloqueada é compatível com `TestClient`.

### Escopo e configuração

- Nenhum `.py` fora de `tests/` alterado (AC5 vazio; `git status` só mostra `tests/**` novos + 3 arquivos permitidos + artefatos `.ai/` do protocolo).
- `pyproject.toml`: só `select`/`ignore` movidos para `[tool.ruff.lint]`; `extend-exclude` permanece em `[tool.ruff]` — correto.
- `.gitignore`: `.env.*` + `!.env.example` — lista ampla verificada acima.
- `docs/desenvolvimento.md`: em português do Brasil; os dois comandos do bloco executam literalmente com exit 0; cobre como rodar, `xfail`, rede bloqueada e como adicionar teste. A linha 30 antiga foi substituída.

## Findings

| # | Arquivo:linha | Severidade | Descrição | Reprodução |
| - | -------------- | ---------- | --------- | ---------- |
| — | — | — | Nenhum finding; nada a corrigir. | — |

## Observações (aceitáveis, sem ação)

1. **Worker registro 1 (AC8):** o texto visível não é "rede bloqueada" e sim `IndexError → RuntimeError → 500` via `aiohappyeyeballs`. Reproduzido exatamente. Aceitável: a prova é que os 4 testes de síntese falham só na cópia com áudio real; nenhum teste da árvore principal depende desse texto.
2. **Worker registro 2 (`![alt](...)` → `"!alt"`):** ordem real das regex em `handle_text.py:24-25` (link antes de imagem) confirma; congelado com comentário `# caracteriza o comportamento atual`. Aceitável.

## Checagens de escopo

- Mudanças ficaram dentro de `allowed_paths`? Sim — `tests/**` (5 arquivos novos), `pyproject.toml`, `.gitignore`, `docs/desenvolvimento.md`. (Artefatos `.ai/` são do protocolo, não do produto.)
- Algum arquivo sensível tocado (.env, credentials, etc.)? Não — só existe `.env.example`, não ignorado; nenhum `.env` criado.

## Checagens de segurança (bloqueante se SIM)

- Segredos/credenciais expostos (token, senha, connection string, chave)? Não — `API_KEY=teste` é valor fictício de teste em `conftest.py`, nunca credencial real.
- Injeção possível (SQL, comando shell, path traversal, XSS)? Não — sem código de produto alterado; testes usam entradas literais.
- Falha de autorização/controle de acesso (rota/função sem checar permissão)? Não — testes só exercitam o comportamento atual; B1 documenta a falha existente como xfail.
- Dependência nova ou script de install sem revisão (RCE/supply-chain)? Não — nenhuma dependência adicionada.
- Log/erro vaza dado sensível? Não — asserções comparam `status_code`, `content-type` e corpo sintético `ID3`.

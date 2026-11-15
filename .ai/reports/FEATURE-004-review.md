# Code Review — FEATURE-004

**Revisor:** code-reviewer
**Data:** 2026-11-15

> Regra fixa: revisor nunca corrige, só reporta.

## Veredito

- [x] Aprovado — segue para `TESTING`
- [ ] Mudanças pedidas — volta para `FIXING`

## Cobertura da spec (itens 1–8) e ACs — com evidência

| Item/AC | Resultado | Evidência (comando + exit) |
| ------- | --------- | ------------------------- |
| Spec 1 — `tts_backends/base.py` com `BackendTTS(Protocol)` (`sintetizar_wav` + `resolver_voz`) | OK | Lido `tts_backends/base.py` (20 linhas, contrato exato da spec) |
| Spec 2 — `tts_backends/edge.py` sem mudar comportamento | OK | `git diff fix/correcoes -- tts_handler.py`: corpo de `gerar_audio_normal` movido tal-qual para `BackendEdge.gerar` (`edge_tts.Communicate(texto, voz, rate=taxa, proxy=PROXY)` + mesma conversão mp3→formato + mesmo `except` com limpeza dos dois temps). `PROXY` lido no import em `edge.py` tal como era no handler; nenhum consumidor de `tts_handler.PROXY` existe (`grep -rn PROXY main.py tests/` vazio). 74 testes antigos passam sem edição (abaixo) |
| Spec 3 — `tts_backends/piper.py` (cache, threads, `length_scale`, `to_thread`, lazy, erros pt-BR) | OK | `grep`: `_CACHE_VOZES` (l.16,102-106), `intra_op_num_threads` (l.73), `escala = 1.0 / velocidade` (l.113), `await asyncio.to_thread(_sintetizar)` (l.145). Topo do módulo só importa stdlib (`asyncio/json/os/tempfile/wave/pathlib`) — `piper`/`onnxruntime` só dentro de `_carregar_voz`/`_sintetizar`. Erros pt-BR: modelo ausente cita caminho + `python scripts/baixar_voz_piper.py <modelo>` + `pip install -r requirements-local.txt` (l.47-54); pacote ausente (l.67,121). `TTS_BACKEND` inválido: `Configuração inválida: TTS_BACKEND='...'` exato (tts_handler.py:57) |
| Spec 4 — `voices_piper.json` (6 apelidos → pt-BR; desconhecido passa direto) | OK | Arquivo lido: alloy/onyx→`pt_BR-faber-medium`, echo/shimmer→`pt_BR-edresson-low`, fable/nova→`pt_BR-cadu-medium`. `resolver_voz` = `self._mapa.get(nome, nome)` + teste `test_piper_voz_desconhecida_passa_direto` verde |
| Spec 5 — handler escolhe backend; pausas e formato valem pros dois; silêncio na taxa do áudio gerado | OK | `obter_backend_nome()` (strip+lower, default `edge`); `gerar_audio` desvia p/ `gerar_audio_piper` só com `piper`. `taxa_silencio` inicial 24000 e atualizada com `audio_segment.frame_rate` após cada segmento nos dois caminhos (tts_handler.py:89/100/119 e 206/218/233). Formatos mp3/wav/opus cobertos por `test_piper_formatos` (verde) |
| Spec 6 — `scripts/baixar_voz_piper.py` manual, nunca em runtime/testes | OK | Script só importa `piper.download_voices.download_voice` no `main()`; nenhum import dele em `tts_handler.py`/`tts_backends/` (`grep` só acha refs no próprio script e nos testes com dublê). Teste com dublê verde |
| Spec 7 — `tests/test_tts_local.py` sem rede/modelo/`.env`, dublê fiel, `skipif` real | OK | 24 testes + 1 `skipif` (`_modelo_real_disponivel()` falso aqui → skip). Dublê tem a forma da API real do `piper-tts 1.8.0`: conferido offline no cache uv (`.../piper/voice.py`): `PiperVoice.load(model_path, config_path=None, use_cuda=False)` monta `InferenceSession(model_or_path, sess_options=SessionOptions(), providers=["CPUExecutionProvider"])` — igual ao `_carregar_voz`; `SynthesisConfig.length_scale` em `piper/config.py`; `synthesize(texto, syn_config)` rende chunks com `sample_rate` + `audio_int16_bytes`; `download_voice(voice, download_dir, force_redownload=False)` igual à chamada do script. `ESPEAK_DATA_DIR` existe em `piper.phonemize_espeak` |
| Spec 8 — `docs/aplicacao/tts-local.md` em pt-BR, sem afirmações falsas | OK | Instalação/vozes/envs/limitações/AC7-pendente/licenças conferem com o código (`PIPER_MODELS_DIR`, `PIPER_THREADS` default nº de núcleos, `length_scale = 1/velocidade`, 6 apelidos). Licença do pacote confirmada offline: `License: GPL-3.0-or-later` (+ `licenses/LICENSE.g2pW-Apache-2.0`) no `METADATA` do `piper_tts-1.8.0.dist-info` no cache uv — bate com o registrado |
| AC1 — suite verde, antigos sem edição | OK | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` → exit 0, `98 passed, 1 skipped`; `--ignore=tests/test_tts_local.py` → exit 0, `74 passed`; `git diff fix/correcoes --name-only -- tests/` = só `?? tests/test_tts_local.py` |
| AC2 — ruff | OK | `.venv/bin/ruff check .` → exit 0, `All checks passed!` |
| AC3 — sem `TTS_BACKEND`, `piper` nunca importado | OK | `.../python -c "import sys; ...; import tts_handler; assert 'piper' not in sys.modules"` → exit 0, sem saída; `import piper` no `.venv` falha (`ModuleNotFoundError`) provando que o handler funciona sem o pacote |
| AC4 — só `allowed_paths`; protegidos intactos | OK | `git diff --name-only fix/correcoes` = `.ai/events.jsonl` (protocolo), `.gitignore` (+`models/`), `tts_handler.py`; untracked só em `allowed_paths`; `test -z "$(git status --porcelain -- main.py config.py .env.example voices.json Dockerfile requirements.txt)"` → exit 0 |
| AC5 — mutações em cópia `.ai/tmp` derrubam testes | OK (reproduzido pelo revisor) | Cópias integrais em `.ai/tmp/revM1` e `.ai/tmp/revM2` (originais intactos): mutação A (`escala = 1.0/velocidade` → `escala = velocidade`) → `pytest -k length_scale` exit 1 (`2 failed, 1 passed`); mutação B (default `"edge"` → `"piper"`) → `tests/test_tts_handler.py` exit 1 (`5 failed, 8 passed`). Logs em `.ai/tmp/revA.log`, `.ai/tmp/revB.log` |
| AC6 — nenhum `.onnx` versionado; `models/` ignorado | OK | `test -z "$(git ls-files \| grep -E '\.onnx')"` → exit 0; `.gitignore` tem `models/`; untracked sem `*.onnx`/`models/` |
| AC7 — medida real de desempenho | PENDENTE (fora dos gates, manual) | Não executado: exige baixar voz da rede com autorização do humano (worker também não baixou; registrado no worker report e nos docs). Não bloqueia este veredito por definição da spec |
| AC8 — sem `__pycache__`, sem `.env` | OK | `find . -name __pycache__ -not -path './.venv/*' ...` → vazio (exit 0); `ls .env` → inexistente |

## Findings

| # | Arquivo:linha | Severidade | Descrição | Reprodução |
| - | -------------- | ---------- | --------- | ---------- |
| 1 | `tts_handler.py:195-240` | baixa | `gerar_audio_com_pausas_piper` duplica ~45 linhas de `gerar_audio_com_pausas` (parse regex, loop, silêncio, export) — só a síntese do segmento difere (`from_wav`+Piper vs `from_mp3`+Edge). A spec pedia mudança mínima; um único caminho de pausas parametrizado pelo sintetizador de segmento eliminaria a duplicação. Funcional e testado — não bloqueante | Leitura: comparar `tts_handler.py:76-139` com `:195-240` |
| 2 | `tts_handler.py:163-193` | baixa | `gerar_audio_normal_piper` (conversão WAV→formato + limpeza de temps) duplica a lógica de `BackendEdge.gerar`. Mesmo comentário do F1: aceitar como está ou extrair helper de conversão; não bloqueante | Leitura: `tts_handler.py:163-193` vs `tts_backends/edge.py:32-76` |
| 3 | `tts_backends/edge.py:84-89` | baixa | `BackendEdge.sintetizar_wav` faz `from tts_handler import velocidade_para_taxa` (import circular contornado com lazy import). Não é usado pelo handler (só cumpre o `Protocol`); inofensivo, mas acopla os módulos. Info | Leitura: `tts_backends/edge.py:79-89` |
| 4 | `tts_handler.py:14` (removido) | info | `PROXY` saiu do `tts_handler` (foi para `tts_backends/edge.py`). Comportamento idêntico (leitura no import nos dois casos) e nenhum consumidor de `tts_handler.PROXY` em `main.py`/`tests/` (grep vazio). Só registro caso algum código externo importe o símbolo | `grep -rn "PROXY" main.py tests/` → vazio; `git diff` do handler |
| 5 | `tts_handler.py:100-104`, `:218-222` | baixa | Se `AudioSegment.from_mp3/from_wav` levantar dentro do loop de pausas, o temp do segmento vaza (unlink só após a leitura). Padrão pré-existente no caminho Edge e replicado no Piper; probabilidade baixa (áudio acabou de ser gerado). Não bloqueante | Leitura dos dois loops de pausas |
| 6 | `tests/test_tts_local.py:29-75` | info | Dublê do `AudioChunk` expõe só `sample_rate` + `audio_int16_bytes` (o real tem também `sample_width`, `sample_channels`, `audio_float_array`, etc.). Suficiente porque a produção só usa esses dois campos (`piper.py:129-130`). Forma da sessão/`SynthesisConfig`/`PiperConfig`/`download_voice` confere com o `piper-tts 1.8.0` real (verificado offline, Spec 7). Sem ação | Comparar fixture `piper_falso` com `piper/voice.py` + `piper/config.py` do cache uv |
| 7 | `tts_handler.py:206` | info | `taxa_silencio` default 24000 no caminho Piper quando o texto não tem nenhum segmento de fala (só `[pause:]`): silêncio a 24 kHz vs voz a 22050 Hz. Diferença inaudível/irrelevante; sem ação | Leitura |

## Checagens de escopo

- Mudanças ficaram dentro de `allowed_paths`? Sim — tracked: só `.gitignore` (+`models/`), `tts_handler.py` e `.ai/events.jsonl` (artefato do protocolo); untracked só em `tts_backends/`, `voices_piper.json`, `requirements-local.txt`, `scripts/`, `tests/test_tts_local.py`, `docs/aplicacao/tts-local.md`, `.specs/`, `.ai/tasks/`, `.ai/reports/`. Protegidos (`main.py`, `config.py`, `.env.example`, `voices.json`, `Dockerfile`, `requirements.txt`) intactos (exit 0)
- Algum arquivo sensível tocado (.env, credentials, etc.)? Não — `.env` nem existe; `.ai/` só tem task/reports/events do protocolo

## Checagens de segurança (bloqueante se SIM)

- [ ] Segredos/credenciais expostos (token, senha, connection string, chave)? Não — grep não acha nada; `.env` inexistente
- [ ] Injeção possível (SQL, comando shell, path traversal, XSS)? Não — sem shell; `PIPER_MODELS_DIR`/`voz` viram `Path` para leitura de `.onnx` (voz desconhecida passa direto como id de modelo por desenho da spec, sem execução)
- [ ] Falha de autorização/controle de acesso (rota/função sem checar permissão)? Não — `main.py` intocado; backend é global por env
- [ ] Dependência nova ou script de install sem revisão (RCE/supply-chain)? Não — única dependência nova é `piper-tts==1.8.0` pinado em `requirements-local.txt` (opcional, fora da imagem/Dockerfile); licença `GPL-3.0-or-later` confirmada offline no METADATA; decisão de uso é do humano (registrado nos docs). `scripts/baixar_voz_piper.py` usa `download_voice` oficial com `ValueError` tratado
- [ ] Log/erro vaza dado sensível? Não — erros carregam só nome do modelo/caminho e traceback sob `LOG_ERROS_DETALHADO`

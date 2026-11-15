# SPEC — Backend de TTS local em CPU (Piper)

**ID:** FEATURE-004 (TTS-LOCAL)
**Data:** 2026-11-14
**Branch:** `feat/feature-004` (worktree separada, parte de `fix/correcoes` por causa dos testes de caracterização)
**Escopo:** permitir gerar áudio **sem o serviço online do Edge**, com um modelo em português rodando só em **CPU**, mantendo o Edge como padrão. Sem GPU, sem rede em runtime.

## 1. Decisões (a confirmar pelo humano na revisão da spec)

- Backend local = **Piper** (`piper-tts`, onnxruntime CPU, vozes pt-BR `faber`, `edresson`, `cadu`, `jeff`). Kokoro/XTTS ficam fora (próxima fase).
- Seleção por variável de ambiente `TTS_BACKEND` = `edge` (padrão, comportamento atual intacto) ou `piper`.
- **Licença:** o `piper-tts` atual pode ser GPL-3 (o MIT era do Piper antigo, arquivado). O worker confere a licença do pacote e das vozes instalados e registra no relatório e em `docs/aplicacao/tts-local.md`; por ser dependência **opcional e não distribuída** na imagem, o projeto (MIT) não a incorpora, mas o humano decide.
- Dependências do Piper **não** entram em `requirements.txt` nem no Dockerfile: vão em `requirements-local.txt` (opcional).
- Modelos `.onnx` ficam em `PIPER_MODELS_DIR` (padrão `./models`), **nunca versionados** (`models/` no `.gitignore` se ainda não estiver).
- Esta feature **não** mexe em `main.py`, `config.py`, `.env.example`, `voices.json`, `Dockerfile` nem `requirements.txt` (evita conflito com FEATURE-003). A leitura das novas variáveis mora no módulo novo.

## 2. Mudanças

1. **Interface de backend** (`tts_backends/base.py`): `class BackendTTS(Protocol)` com `async def sintetizar_wav(texto, voz, velocidade) -> str` (caminho de um WAV temporário) e `def resolver_voz(nome) -> str`.
2. **Backend Edge** (`tts_backends/edge.py`): move para cá, **sem mudar comportamento**, a chamada ao `edge_tts.Communicate` hoje em `gerar_audio_normal`. Os testes de caracterização existentes continuam verdes sem alteração.
3. **Backend Piper** (`tts_backends/piper.py`): carrega o modelo sob demanda (cache em memória, um por voz), importa `piper` de forma preguiçosa (número de threads do onnxruntime via `PIPER_THREADS`, padrão = todos os núcleos; erro claro em pt-BR se o pacote ou o modelo faltarem: cita o caminho esperado e o comando de instalação). Velocidade → `length_scale = 1 / velocidade` (faixa 0.25–2.0 já validada pela rota). Síntese roda em `asyncio.to_thread` para não bloquear o event loop.
4. **Mapeamento de vozes Piper** em `voices_piper.json` (novo): apelidos OpenAI (`alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`) → nome do modelo Piper pt-BR. Voz desconhecida é repassada como nome de modelo.
5. **`tts_handler.py`**: `gerar_audio` escolhe o backend por `TTS_BACKEND` (valor inválido → `RuntimeError` com `Configuração inválida: TTS_BACKEND='x' (esperado edge ou piper)`). Pausas `[pause: Xs]` e conversão de formato (pydub/ffmpeg) continuam no handler e valem para os dois backends; o silêncio usa a **taxa de amostragem do áudio gerado** (não mais 24000 fixo). Mudança mínima: não refatorar o que não for necessário.
6. **Download de vozes** (`scripts/baixar_voz_piper.py`, novo): baixa `.onnx` + `.onnx.json` da voz pedida para `PIPER_MODELS_DIR`. Uso manual, nunca chamado em runtime nem nos testes.
7. **Testes** (`tests/test_tts_local.py`, novo): sem rede, sem modelo real, sem `.env`. Backend Piper testado com um **dublê** do módulo `piper` (monkeypatch em `sys.modules`) que devolve PCM sintético; cobrir: seleção de backend (edge padrão, piper, inválido), mapeamento de apelidos, `length_scale` por velocidade, erro claro com modelo ausente, pausas com backend Piper (duração total = fala + silêncio), formatos mp3/wav/opus pela conversão existente, e que o backend Edge segue sendo o padrão sem `TTS_BACKEND`. Um teste de integração real com Piper é marcado `skipif` quando o modelo/pacote não existe.
8. **Docs** (`docs/aplicacao/tts-local.md`, novo): como instalar (`pip install -r requirements-local.txt`), baixar uma voz, ligar `TTS_BACKEND=piper`, limitações (menos vozes, sem estilo/emoção, soa menos natural que o Edge) e medida de desempenho (ver AC7). Português do Brasil.

## 3. Critérios de aceitação

- AC1: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q` → exit 0, 0 failed, 0 xpassed; os testes que já existiam seguem passando **sem edição**.
- AC2: `.venv/bin/ruff check .` → exit 0.
- AC3: sem `TTS_BACKEND` definido, nenhum teste nem import toca `piper`; `python -c "import tts_handler"` funciona **sem** `piper-tts` instalado.
- AC4: `git diff --name-only <base>` só toca `allowed_paths`; `main.py`, `config.py`, `.env.example`, `voices.json`, `Dockerfile`, `requirements.txt` intactos.
- AC5 (mutação em cópia em `.ai/tmp/`): trocar `1 / velocidade` por `velocidade`, ou o padrão `edge` por `piper`, derruba ≥ 1 teste em cada caso.
- AC6: nenhum arquivo `.onnx`/`.onnx.json` versionado (`git ls-files | grep -E "\.onnx"` vazio) e `models/` ignorado pelo git.
- AC7 (manual, fora dos `required_checks`): com `piper-tts` e a voz `pt_BR-faber-medium` baixadas, `TTS_BACKEND=piper` gera um WAV de um parágrafo (~300 caracteres) **só com CPU** (`CUDA_VISIBLE_DEVICES=""`). Medir em **dois cenários** e registrar no relatório o tempo de síntese, a duração do áudio e o fator de tempo real: (a) sem limite; (b) **simulando a VPS de destino (2 vCPUs ≈ 2 threads de 1 núcleo físico)**: `taskset -c <A>,<B>` com `A` e `B` **threads irmãos do mesmo núcleo físico** (descobrir com `lscpu -e=CPU,CORE`: mesma coluna CORE) e `PIPER_THREADS=2`. Rodar a medida **3 vezes** e registrar a pior. Meta: fator de tempo real < 0,5 em (b), para deixar folga a CPU compartilhada da VPS, ao uvicorn e ao ffmpeg; se não for, registrar o valor real sem mascarar. Registrar também o pico de memória (`/usr/bin/time -v`). Requer rede só para baixar a voz; o worker avisa o humano antes de baixar.
- AC8: nenhum `__pycache__` fora de `.venv`/`.estrutura`/`.ai/tmp` e `.env` inexistente ao final.

## 4. Fora do escopo

Kokoro, XTTS e qualquer modelo que exija GPU; clonagem de voz; troca de backend por requisição (o backend é global, por ambiente); mudanças no Dockerfile/CI; streaming.

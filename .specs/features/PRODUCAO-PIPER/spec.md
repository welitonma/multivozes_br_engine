# SPEC — Piper em produção: voz padrão faber, imagem única e CI

**ID:** FEATURE-006 (PRODUCAO-PIPER)
**Data:** 2026-11-14
**Branch:** `feat/feature-006` (parte de `feat/feature-004`, que traz o backend Piper)
**Objetivo do humano:** o backend Piper funcionar **na API atual, sem instalar nada à parte**: a mesma imagem Docker de hoje traz Piper + voz `faber`; o backend se escolhe só por variável de ambiente. Urgência alta (produção).

## 1. Decisões do humano (já tomadas)

- Imagem **única**, publicada como hoje, contendo Piper e a voz `pt_BR-faber-medium`. `TTS_BACKEND=edge` continua o padrão: sem a variável, o comportamento é idêntico ao atual.
- A voz padrão do Piper é a `faber`.
- O humano aceitou distribuir o `piper-tts` (GPL-3.0-or-later) na imagem pública (decisão registrada; o worker cumpre as obrigações de aviso do item 6).
- Spec **sem revisão de spec** (pedido de urgência); a revisão de código e os gates seguem normais.

## 2. Mudanças

1. **Voz padrão (`tts_backends/piper.py`, `voices_piper.json`):** nova variável `PIPER_DEFAULT_VOICE` (padrão `pt_BR-faber-medium`). `resolver_voz(nome)`: (a) apelido do mapa -> modelo; (b) nome **vazio** ou **de voz do Edge** (regex `^[a-z]{2}-[A-Z]{2}-.+Neural$`, ex.: `pt-BR-ThalitaMultilingualNeural`, o `DEFAULT_VOICE` atual) -> `PIPER_DEFAULT_VOICE`; (c) qualquer outro nome -> repassado como id de modelo (como hoje). Assim a API sem `voice` e com `TTS_BACKEND=piper` fala com a `faber`. Não tocar `main.py`/`config.py`. Apelidos femininos (`nova`, `shimmer`, `alloy`...) passam a apontar para a `faber` (não há voz Piper feminina pt-BR): atualizar `voices_piper.json` para `alloy, nova, shimmer, onyx, echo, fable` -> `pt_BR-faber-medium` **somente se** as outras vozes não estiverem baixadas na imagem (a imagem só traz a faber); registrar isso na doc.
2. **`Dockerfile`:** manter `python:3.11-slim`, ffmpeg e o `HEALTHCHECK`. Além do `requirements.txt`, instalar `requirements-local.txt` (Piper). Instalar bibliotecas de sistema que o onnxruntime/piper exijam (o worker descobre construindo; ex.: `libgomp1`). Baixar a voz **na construção**: copiar `scripts/baixar_voz_piper.py` antes e rodar `python scripts/baixar_voz_piper.py pt_BR-faber-medium --dir /app/models` numa camada própria (cache), **antes** do `COPY . .`. Definir `ENV TTS_BACKEND=edge PIPER_MODELS_DIR=/app/models`. Não definir `PIPER_THREADS` (o humano define no `docker run`; padrão = todos os núcleos). Ordem das camadas pensada para cache.
3. **arm64:** o CI constrói amd64 e arm64. O worker confere se o `piper-tts==1.8.0` e o `onnxruntime` têm wheel aarch64 (`pip download --only-binary=:all: --platform manylinux_2_28_aarch64 --python-version 3.11 --no-deps ...`). Se **não** houver: no Dockerfile usar `ARG TARGETARCH` e instalar o Piper só em amd64; em arm64 a imagem fica Edge-only e `TTS_BACKEND=piper` deve falhar com a mensagem clara já existente; documentar. Se houver wheel, instalar nas duas.
4. **`.dockerignore`:** acrescentar `models/`, `tests/`, `.github/`, `*.md` desnecessários **sem** ignorar `scripts/`, `voices_piper.json`, `voices.json`, `requirements*.txt` nem `tts_backends/`. Conferir que nada necessário em runtime foi ignorado.
5. **CI (`.github/workflows/publish.yml`):** (a) novo job `testes` (ubuntu, Python 3.11, `pip install -r requirements-dev.txt`, `ruff check .`, `pytest -q`) em PR e push; (b) `build-and-push` passa a depender de `testes` (`needs`); (c) o label `org.opencontainers.image.licenses` passa a `MIT AND GPL-3.0-or-later`; (d) o job de build continua não publicando em PR. Não alterar secrets, gatilhos nem `schedule`. YAML validado localmente (`python -c "import yaml; yaml.safe_load(...)"`).
6. **Licenças:** criar `THIRD_PARTY_NOTICES.md` com piper-tts (GPL-3.0-or-later, fonte `github.com/OHF-Voice/piper1-gpl`), espeak-ng (GPL-3.0-or-later, bundled no piper-tts), onnxruntime (MIT), voz `faber` (dataset CC0; base Hi-Fi TTS 92: **licença a confirmar**, escrever "a confirmar"), com a nota de que a imagem inclui esses componentes e o código-fonte deles está nas URLs indicadas. Copiá-lo para dentro da imagem (`COPY` já cobre) e linkar no README. **Não** afirmar nada jurídico além do que o pacote declara.
7. **`.env.example`:** acrescentar, comentadas e em português, `TTS_BACKEND`, `PIPER_THREADS`, `PIPER_MODELS_DIR`, `PIPER_DEFAULT_VOICE`.
8. **Docs:** `docs/aplicacao/deploy.md` e `tts-local.md` (imagem única, `docker run -e TTS_BACKEND=piper -e PIPER_THREADS=2 ...`, systemd com venv, tamanho da imagem medido, como voltar ao Edge) e uma seção curta no `README.md`. Português do Brasil.
9. **Testes** (`tests/test_tts_voz_padrao.py`, novo; testes anteriores **sem edição**): `resolver_voz` com `pt-BR-ThalitaMultilingualNeural` e com vazio -> faber; apelido -> mapa; nome de modelo -> passa direto; `PIPER_DEFAULT_VOICE` sobrescreve; sem rede, sem modelo, dublê do `piper`.

## 3. Critérios de aceitação

- AC1: `pytest -q` verde (0 failed), todos os testes anteriores sem edição; `ruff check .` limpo.
- AC2: `docker build -t multivozes-test .` conclui (amd64) e o tamanho da imagem é registrado (comparar com a base `python:3.11-slim`).
- AC3: container **sem** `TTS_BACKEND`: `POST /v1/models`-like `GET /v1/models` responde 200 (HEALTHCHECK) e o backend ativo é o Edge (checado por `docker run ... python -c` sem rede nem chamada ao serviço).
- AC4: container com `-e TTS_BACKEND=piper -e PIPER_THREADS=2 --cpuset-cpus 0,1 -e REQUIRE_API_KEY=false` (sem rede: `--network none` na síntese): `POST /v1/audio/speech` **sem campo `voice`** devolve 200 com áudio mp3 não vazio e duração > 3 s (conferir com ffprobe); repetir com `voice: "nova"` e com texto contendo `[pause: 1s]`. Registrar tempo e RTF.
- AC5: `python -c "import yaml; yaml.safe_load(open('.github/workflows/publish.yml'))"` ok; `grep -n "needs" .github/workflows/publish.yml` mostra a dependência do build nos testes; `schedule`/gatilhos/secrets inalterados (`git diff` conferido).
- AC6: wheel aarch64 verificada e a decisão do item 3 aplicada e documentada.
- AC7: `git diff --name-only feat/feature-004` só toca `allowed_paths`; `main.py`, `config.py`, `voices.json` e `requirements.txt` intactos; nenhum `.onnx` versionado; `.dockerignore` não ignora nada necessário em runtime (provado pelo AC4).
- AC9 (**teste ponta a ponta com a API real, obrigatório**): com o container da imagem construída (Piper, `--cpuset-cpus 0,1`, `PIPER_THREADS=2`, `--network none` na síntese) e a API ouvindo, registrar com `curl` (comando + status HTTP + tamanho/duração do áudio via `ffprobe`): (1) `GET /v1/models` 200; (2) `REQUIRE_API_KEY=true` com `API_KEY`: sem cabeçalho -> 401, chave errada -> 401, chave certa -> 200; (3) `POST /v1/audio/speech` com `response_format` mp3, wav, opus, aac e flac (os formatos que a API aceita; os que falharem entram no relatório com a causa, sem ser corrigidos fora do escopo); (4) `speed` 0.5, 1.0 e 2.0 (a duração deve variar na direção certa) e `speed` 3.0 -> 422; (5) texto com `[pause: 2s]` e `[pause: 700ms]`: duração >= fala + pausas; (6) `input` vazio -> 400; (7) `voice` ausente, `nova`, `onyx` e um nome inexistente (erro claro, não 500 genérico sem mensagem); (8) **2 requisições simultâneas** com texto longo: ambas 200 e a API continua respondendo `GET /v1/models` durante a síntese (prova que a síntese não bloqueia o servidor); (9) texto longo (~2000 caracteres): 200 e tempo/RTF/memória do container (`docker stats --no-stream`); (10) logs do container sem traceback inesperado e sem arquivos temporários acumulando em `/tmp` depois das chamadas. Tudo isso em tabela no relatório com saída real. O teste com o **Edge real** (rede) fica por conta do orquestrador depois, não do worker.
- AC8: nenhum `__pycache__` fora de `.venv`/`.estrutura`/`.ai/tmp`, `.env` inexistente, imagens/containers de teste removidos ao final (`docker rm -f` e `docker rmi` só do que o worker criou, por nome exato).

## 4. Fora do escopo

Kokoro (FEATURE-005); push, PR e merge (humano); alterar secrets do GitHub; troca de backend por requisição; Python além do 3.11.

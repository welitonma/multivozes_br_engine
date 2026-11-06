# Unidade `deploy` — Dockerfile, systemd, `.env.example`, dependências e CI

> Fontes: `Dockerfile` (38 linhas), `multivozes_br_engine.service` (53 linhas),
> `.env.example` (52 linhas), `requirements.txt` (15 linhas),
> `.github/workflows/publish.yml` (89 linhas).
> Nenhum desses arquivos define funções, classes ou rotas HTTP — são artefatos de
> empacotamento, operação e integração contínua. A aplicação em si está documentada
> em `main.md`, `tts-handler.md` e `texto-config-utils.md`.

## 1. `Dockerfile` — imagem de produção

**Propósito:** construir a imagem Docker da API (Python + FFmpeg) que executa
`python main.py` na porta 5050.

**Passo a passo (na ordem do arquivo):**

| Linha(s) | O que faz |
|---|---|
| `Dockerfile:1` | Base `python:3.11-slim` |
| `Dockerfile:4-5` | Labels `maintainer="welitonma"` e descrição da API |
| `Dockerfile:8-12` | `apt-get install ffmpeg` (essencial para o `pydub` converter áudio) e limpeza de `/var/lib/apt/lists/*` |
| `Dockerfile:15` | `WORKDIR /app` |
| `Dockerfile:18` | `COPY requirements.txt .` antes do restante (cache de layer) |
| `Dockerfile:21-22` | Atualiza o `pip` e instala `requirements.txt` com `--no-cache-dir` |
| `Dockerfile:25` | `COPY . .` — copia todo o código da aplicação |
| `Dockerfile:28` | `mkdir -p /tmp/tts_audio` — diretório de arquivos temporários de áudio |
| `Dockerfile:31` | `EXPOSE 5050` (documental; não publica a porta sozinho) |
| `Dockerfile:34-35` | `HEALTHCHECK`: a cada 30 s (timeout 10 s, 3 tentativas, início após 5 s) faz `GET http://localhost:5050/v1/models` via `urllib.request`; falha se o endpoint não responder |
| `Dockerfile:38` | `CMD ["python", "main.py"]` — ponto de entrada |

**Fluxo de dados:** build copia `requirements.txt` → instala dependências →
copia o código → em runtime o contêiner escreve áudios temporários em
`/tmp/tts_audio` e serve HTTP na porta 5050.

**Como executar (não verificado — comandos derivados do arquivo, não executados
neste despacho):**

```bash
docker build -t multivozes-br-engine .
docker run -p 5050:5050 --env-file .env multivozes-br-engine
curl http://localhost:5050/v1/models  # mesmo endpoint do HEALTHCHECK
```

## 2. `multivozes_br_engine.service` — serviço systemd

**Propósito:** modelo de unit systemd para rodar a API direto no host (sem
Docker), com reinício automático. O cabeçalho (`multivozes_br_engine.service:1-16`)
explica a instalação: copiar o conteúdo para
`/etc/systemd/system/multivozes_br_engine.service`, ajustar os campos marcados
com "==> ALTERE AQUI", depois `systemctl daemon-reload`, `enable` e `start`.

**Seções e diretivas:**

| Linha(s) | Seção/diretiva | Valor e observação |
|---|---|---|
| `multivozes_br_engine.service:18-21` | `[Unit]` | `Description=Serviço para o Multivozes BR Engine`, `After=network.target` |
| `multivozes_br_engine.service:27` | `User` | `root` (o próprio comentário no arquivo recomenda criar um usuário dedicado em vez de `root`) |
| `multivozes_br_engine.service:31` | `Group` | `root` |
| `multivozes_br_engine.service:37` | `WorkingDirectory` | `/opt/tts` — é preciso ajustar para o caminho real do clone |
| `multivozes_br_engine.service:42` | `Environment` | `VIRTUAL_ENV=/opt/tts/venv` — aponta o venv dentro do `WorkingDirectory` |
| `multivozes_br_engine.service:47` | `ExecStart` | `/bin/bash -c 'source venv/bin/activate && python3 main.py'` — ativa o venv relativo (`venv/bin/activate`) e executa `main.py` com o Python do venv |
| `multivozes_br_engine.service:49-50` | Reinício | `Restart=always`, `RestartSec=10` |
| `multivozes_br_engine.service:52-53` | `[Install]` | `WantedBy=multi-user.target` |

**Como executar (não verificado — derivado dos comentários do próprio arquivo):**

```bash
sudo nano /etc/systemd/system/multivozes_br_engine.service  # colar o conteúdo ajustado
sudo systemctl daemon-reload
sudo systemctl enable multivozes_br_engine
sudo systemctl start multivozes_br_engine
systemctl status multivozes_br_engine
```

## 3. `.env.example` — variáveis de ambiente (modelo)

**Propósito:** modelo de configuração lido pela aplicação via `python-dotenv`
(dependência em `requirements.txt:13`). Copie para `.env` e ajuste. Os padrões
abaixo foram confirmados contra `config.py:1-13` (`DEFAULT_CONFIGS`), que define
os mesmos valores quando a variável não existe.

| Variável | Linha no `.env.example` | Valor de exemplo/padrão | Confirmado em `config.py` |
|---|---|---|---|
| `PORT` | `.env.example:4` | `5050` | `config.py:3` → `5050` |
| `API_KEY` | `.env.example:12` | placeholder ilustrativo (trocar por chave real) | `config.py:4` → `None` (ou seja: o exemplo traz texto de preenchimento, o código assume ausente) |
| `REQUIRE_API_KEY` | `.env.example:16` | `True` | `config.py:13` → `True` |
| `DEFAULT_VOICE` | `.env.example:23` | `pt-BR-ThalitaMultilingualNeural` | `config.py:7` → idem |
| `DEFAULT_RESPONSE_FORMAT` | `.env.example:26` | `mp3` | `config.py:8` → `mp3` |
| `DEFAULT_SPEED` | `.env.example:29` | `1.0` | `config.py:9` → `1.0` |
| `DEFAULT_LANGUAGE` | `.env.example:33` | `pt-BR` (`all` = todas) | `config.py:10` → `pt-BR` |
| `REMOVE_FILTER` | `.env.example:40` | `False` | ver `texto-config-utils.md` |
| `DETAILED_ERROR_LOGGING` | `.env.example:44` | `True` | ver `texto-config-utils.md` |
| `EXPAND_API` | `.env.example:47` | `True` | ver `texto-config-utils.md` |
| `PROXY` | `.env.example:51-52` | comentado (só descomentar se precisar de proxy) | não verificado |

**Observações:**

- O cabeçalho de cada bloco no `.env.example` documenta o significado
  (ex.: `REQUIRE_API_KEY=True` é "ALTAMENTE recomendado" em produção;
  `API_KEY` vai no cabeçalho `Authorization: Bearer ...`).
- Semântica de `True`/`False`: **não verificada** neste despacho — a conversão
  de string para booleano vive em `config.py` (ver `texto-config-utils.md`).
- Nunca commitar o `.env` real; só o `.env.example` é versionado.

## 4. `requirements.txt` — dependências

**Propósito:** pins instalados pelo `Dockerfile:21-22`. São 13 pacotes
(`requirements.txt:1-15`):

| Linha(s) | Pacote | Versão |
|---|---|---|
| `requirements.txt:1` | `fastapi` | `==0.111.0` |
| `requirements.txt:2` | `uvicorn[standard]` | `==0.29.0` (servidor ASGI) |
| `requirements.txt:3` | `pydantic` | `==2.7.1` |
| `requirements.txt:4` | `loguru` | `==0.7.2` (logs) |
| `requirements.txt:5` | `edge-tts` | `>=7.3.1,<8` (única faixa flexível; motor TTS) |
| `requirements.txt:6` | `anyio` | `==4.3.0` |
| `requirements.txt:7` | `starlette` | `==0.37.2` |
| `requirements.txt:8` | `openai` | `==1.25.1` |
| `requirements.txt:9` | `async-timeout` | `==4.0.3` |
| `requirements.txt:10` | `emoji` | `==2.12.1` (filtro de emojis) |
| `requirements.txt:11` | `aiofiles` | `==23.2.1` |
| `requirements.txt:12` | `aiohttp` | `==3.11.10` |
| `requirements.txt:13` | `python-dotenv` | `==1.0.1` (lê o `.env`) |
| `requirements.txt:15` | `pydub` | `==0.25.1` (conversão de áudio; precisa do FFmpeg de `Dockerfile:8-12`) |

**Dependência de sistema (fora do pip):** `ffmpeg` via apt (`Dockerfile:8-12`).

## 5. `.github/workflows/publish.yml` — CI de build e push

**Propósito:** workflow "Docker Build and Push - Multivozes"
(`.github/workflows/publish.yml:1`) que constrói a imagem multi-arquitetura e
publica no Docker Hub.

**Disparos (`publish.yml:3-12`):** push na branch `master`, tags `v*.*.*`,
pull requests contra `master`, disparo manual (`workflow_dispatch`) e agendado
toda segunda às 06:00 UTC (`cron: '0 6 * * 1'`) para reconstruir com o
`edge-tts` mais recente.

**Job `build-and-push` (`publish.yml:14-16`, runner `ubuntu-latest`,
environment `DockerHUB`):**

| Passo | Linha(s) | O que faz |
|---|---|---|
| Checkout | `publish.yml:19-21` | `actions/checkout@v4` |
| Metadados | `publish.yml:24-41` | `docker/metadata-action@v5`; imagem `${{ secrets.DOCKERHUB_USERNAME }}/multivozes-br-engine`; tags por branch, PR, semver (`version`, `major.minor`, `major`), SHA e `latest` na branch padrão; labels OCI (título, descrição, `vendor=welitonma`, licença MIT) |
| QEMU | `publish.yml:44-46` | `docker/setup-qemu-action@v3` (build multi-plataforma) |
| Buildx | `publish.yml:49-51` | `docker/setup-buildx-action@v3` |
| Login | `publish.yml:54-58` | `docker/login-action@v3` com `secrets.DOCKERHUB_USERNAME` / `secrets.DOCKERHUB_TOKEN` |
| Build + push | `publish.yml:61-72` | `docker/build-push-action@v6` com `context: .`, `file: ./Dockerfile`, `platforms: linux/amd64,linux/arm64`; `push` só quando não é PR (`publish.yml:66`); `no-cache` apenas no agendado (`publish.yml:69`); cache GHA (`cache-from`/`cache-to`, `publish.yml:70-71`); `provenance: false` (`publish.yml:72`) |
| Descrição no Hub | `publish.yml:75-88` | espera 10 s e atualiza a descrição do repositório via `peter-evans/dockerhub-description@v4` com o `README.md`; `continue-on-error: true` (não falha o workflow) |

**Segredos exigidos (não verificados — apenas referenciados no arquivo):**
`DOCKERHUB_USERNAME` e `DOCKERHUB_TOKEN`.

## O que não foi verificado

- Build da imagem Docker, `docker run` e resposta do `HEALTHCHECK` — comandos
  acima são derivados dos arquivos, não executados (proibido subir servidor /
  instalar dependência neste despacho).
- Ativação real do serviço systemd (`systemctl start/status`).
- Conversão exata de `"True"`/`"False"` do `.env` para booleano (vive em
  `config.py`, coberto em `texto-config-utils.md`).
- Execução do workflow no GitHub Actions; segredos `DOCKERHUB_*` não lidos.

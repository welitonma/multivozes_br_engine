# Unidade `docs-existentes` — inventário da documentação já presente no repositório

> Fontes (somente leitura; nada aqui foi alterado): `README.md` (251 linhas),
> `API_USAGE_GUIDE.md` (94 linhas), `BEGINNERS_GUIDE.md` (271 linhas),
> `N8N-INTEGRATION.md` (61 linhas), `VOICES.md` (66 linhas), `SUPPORT.md`
> (37 linhas), `CHANGELOG.md` (31 linhas). Total: 811 linhas.
> Esta unidade documenta **o que cada guia contém** (propósito, endpoints,
> parâmetros, variáveis e procedimentos descritos) com citações `arquivo:linha`.
> O comportamento do código em si está em `main.md`, `tts-handler.md` e
> `texto-config-utils.md`; divergências entre guias e código estão marcadas como
> **não verificado** quando exigiriam executar algo.

## Mapa de leitura sugerido

1. `README.md` — visão geral e instalação rápida.
2. `BEGINNERS_GUIDE.md` — passo a passo detalhado (VPS ou WSL2).
3. `API_USAGE_GUIDE.md` — como chamar `POST /v1/audio/speech`.
4. `VOICES.md` — quais vozes usar no parâmetro `voice`.
5. `N8N-INTEGRATION.md` — como plugar no n8n.
6. `CHANGELOG.md` — o que mudou na 2.0.0.
7. `SUPPORT.md` — onde pedir ajuda.

O índice oficial vive em `README.md:80-90` ("📚 Documentação Completa").

## 1. `README.md` — porta de entrada

**Propósito:** apresentar o projeto (API de TTS auto-hospedada, compatível com
OpenAI, vozes neurais gratuitas da Microsoft Edge — `README.md:37`), listar
funcionalidades, pré-requisitos, instalação rápida e as 3 formas de executar.

**Conteúdo por trecho:**

| Linha(s) | Conteúdo |
|---|---|
| `README.md:41-49` | Novidades da 2.0.0: vozes multilinguais, mapeamento via `voices.json`, conversão real com `pydub`+`ffmpeg`; aponta para o `CHANGELOG.md` |
| `README.md:53-61` | Funcionalidades: compatibilidade OpenAI, async, filtro de emoji/Markdown, Bearer Token, configuração via `.env` |
| `README.md:64-77` | Tabela comparando "API sozinha" x "Aliança MultiVozes + Engine" (gestão de usuários, créditos, interface visual, histórico, painel admin — itens do Painel, **não** desta API) |
| `README.md:93-98` | Pré-requisitos: Python 3.8+, Git, FFmpeg |
| `README.md:101-130` | Instalação rápida: clonar em `/opt`, venv, `pip install -r requirements.txt`, `cp .env.example .env`, editar `voices.json` |
| `README.md:137-157` | Opção 1 de execução: `source venv/bin/activate` + `python main.py` (terminal aberto) |
| `README.md:159-191` | Opção 2: tmux (`tmux new -s multivozes`, detach com `Ctrl+B, D`, `tmux attach -t multivozes`); avisa que não sobrevive a reboot |
| `README.md:193-238` | Opção 3: systemd em "uma linha" (serviço `multivozes`, `WorkingDirectory=/opt/multivozes_br_engine`, `RestartSec=5`, logs no journal) + comandos `status`/`journalctl`/`stop`/`restart` |
| `README.md:240-247` | Acesso: porta padrão **5050** e Swagger em `http://localhost:5050/docs` |

**Divergências internas observadas (só leitura, sem execução):**

- O bloco "▶️ Executando o Servidor" e a "Opção 1" aparecem **duplicados**
  (`README.md:133-145` repetem o mesmo título e conteúdo).
- O service da "Opção 3" (`README.md:193-238`, nome `multivozes`,
  `/opt/multivozes_br_engine`, `RestartSec=5`) **difere** do arquivo
  `multivozes_br_engine.service` (nome `multivozes_br_engine`, `/opt/tts`,
  `RestartSec=10`) — ver `deploy.md`. Qual usar em produção: **não verificado**.
- Pré-requisito diz Python 3.8+ (`README.md:95`), mas a imagem Docker usa
  `python:3.11-slim` (`Dockerfile:1`) — compatibilidade com 3.8: **não verificada**.

## 2. `BEGINNERS_GUIDE.md` — instalação para iniciantes

**Propósito:** guia passo a passo para quem está começando, incluindo conceitos
básicos (VPS, terminal, SSH, venv, Bearer Token em
`BEGINNERS_GUIDE.md:7-15`).

**Conteúdo por trecho:**

| Linha(s) | Conteúdo |
|---|---|
| `BEGINNERS_GUIDE.md:17-58` | Opção 1 (VPS Ubuntu/Debian): SSH, `apt update && upgrade`, instalar `git python3 python3-venv python3-pip ffmpeg`, clonar, venv, `pip install -r requirements.txt`, `cp .env.example .env` |
| `BEGINNERS_GUIDE.md:60-82` | Geração da `API_KEY`: `echo "API_KEY=sk-$(openssl rand -hex 32)" \| tee -a .env` ou edição manual com `nano .env` |
| `BEGINNERS_GUIDE.md:84-172` | Execução: Opção A terminal aberto, Opção B tmux, Opção C systemd em uma linha (mesmo bloco do README, serviço `multivozes`) + comandos de gerenciamento (`status`, `journalctl -u multivozes -f`, `stop`, `restart`, `disable`) |
| `BEGINNERS_GUIDE.md:174-203` | Opção 2 (Windows + WSL2): `wsl --install`, abrir Ubuntu, criar usuário, depois seguir a Opção 1 a partir do passo 2 |
| `BEGINNERS_GUIDE.md:206-232` | Teste: Swagger em `http://localhost:5050/docs` e exemplo `curl POST /v1/audio/speech` com voz `pt-BR-FranciscaNeural` salvando `teste.mp3` |
| `BEGINNERS_GUIDE.md:234-256` | Problemas comuns: instalar Docker via `get.docker.com`, `sudo` para permissão, trocar `PORT=5050` por `8080` se a porta estiver ocupada, usar tmux/systemd para persistência |
| `BEGINNERS_GUIDE.md:258-266` | Próximos passos: `voices.json`, n8n/Make, Painel MultiVozes, `API_USAGE_GUIDE.md` |

**Observação:** os comandos acima foram apenas lidos, **não executados** neste
despacho — eficácia real: **não verificada**.

## 3. `API_USAGE_GUIDE.md` — como chamar a API

**Propósito:** referência de uso do endpoint principal com exemplos `curl` e Python.

**Conteúdo por trecho:**

| Linha(s) | Conteúdo |
|---|---|
| `API_USAGE_GUIDE.md:7-15` | Endpoint `POST /v1/audio/speech`; parâmetros: `input` (obrigatório), `model` (`tts-1`/`tts-1-hd`), `voice` (apelido ou nome técnico; padrão do `.env`), `response_format` (`mp3`, `opus`, `aac`, `flac`, `wav`, `pcm`; padrão `mp3`), `speed` (`1.0` = normal) |
| `API_USAGE_GUIDE.md:23-37` | Exemplo 1 (`curl`): voz `alloy`, texto multilíngue PT+EN, saída `audio_multilingual.mp3`; exige `Authorization: Bearer SUA_CHAVE_API_AQUI` |
| `API_USAGE_GUIDE.md:39-55` | Exemplo 2 (`curl`): voz `echo` com `"response_format": "flac"`, saída `audio.flac` |
| `API_USAGE_GUIDE.md:57-94` | Exemplo Python com `requests` (stream + `shutil.copyfileobj`), voz `shimmer`, tratamento de `status_code != 200` e `RequestException` |

**Não verificado:** execução real dos exemplos (proibido subir servidor/chamar
rede neste despacho); correspondência exata dos parâmetros com `main.py` deve ser
conferida em `main.md`.

## 4. `VOICES.md` — catálogo de vozes

**Propósito:** referência rápida das vozes recomendadas e do mapeamento
apelido OpenAI → voz Edge-TTS.

**Conteúdo por trecho:**

| Linha(s) | Conteúdo |
|---|---|
| `VOICES.md:5` | Dica: descobrir mais vozes com `edge-tts --list-voices` |
| `VOICES.md:9-21` | Mapeamento padrão: `alloy`→`en-US-AndrewMultilingualNeural`, `echo`→`en-US-BrianMultilingualNeural`, `fable`→`de-DE-SeraphinaMultilingualNeural`, `onyx`→`de-DE-FlorianMultilingualNeural`, `nova`→`en-US-EmmaMultilingualNeural`, `shimmer`→`en-US-AvaMultilingualNeural` (personalizável em `voices.json`) |
| `VOICES.md:26-40` | Multilíngues (12 vozes, inclui `pt-BR-ThalitaMultilingualNeural`) |
| `VOICES.md:42-49` | Português (5 vozes: Antonio, Francisca, Thalita, Duarte, Raquel) |
| `VOICES.md:51-57` | Espanhol (4 vozes) |
| `VOICES.md:59-66` | Inglês (6 vozes) |

**Não verificado:** se o mapeamento impresso aqui é idêntico ao `voices.json`
efetivo do repositório (o `voices.json` está coberto em `texto-config-utils.md`).

## 5. `N8N-INTEGRATION.md` — integração com n8n

**Propósito:** plugar a Engine no n8n (testado na versão `1.110.1`,
`N8N-INTEGRATION.md:9`) usando o nó nativo da OpenAI.

**Conteúdo por trecho:**

| Linha(s) | Conteúdo |
|---|---|
| `N8N-INTEGRATION.md:13-24` | Passo 1 — credencial "OpenAI API": nome `Multivozes BR Engine`, API Key do `.env`, Base URL `<servidor>/v1` (ex. `http://localhost:5050/v1`), Organization ID em branco |
| `N8N-INTEGRATION.md:26-37` | Passo 2 — nó OpenAI: Resource `Audio`, Operation `Speech`, Model `tts-1`, Input com expressão `{{ $json.text }}`, Voice da tabela/`VOICES.md` |
| `N8N-INTEGRATION.md:39-53` | Tabela de vozes mapeadas (mesmo mapeamento do `VOICES.md`) com gênero; lembra que `voices.json` permite personalizar |
| `N8N-INTEGRATION.md:55-60` | Passo 3 — `Execute Workflow`; o áudio volta como buffer binário no nó |

**Não verificado:** teste real no n8n 1.110.1 (exigiria rede e o produto).

## 6. `CHANGELOG.md` — histórico de versões

**Propósito:** histórico no formato Keep a Changelog + versionamento semântico
(`CHANGELOG.md:3-6`).

**Conteúdo:** versão `[2.0.0] - 2025-10-02` (`CHANGELOG.md:10`) — adicionados:
vozes multilinguais (Thalita, Giuseppe, William, Hyunsu), mapeamento externo em
`voices.json`, criação do próprio changelog; alterados: conversão real de áudio
via `pydub`+`ffmpeg`, reescrita da documentação, `pydub` no `requirements.txt`
(`CHANGELOG.md:12-29`). Série 1.x resumida como base OpenAI-compatível
(`CHANGELOG.md:31`).

**Discrepância verificada em disco:** o changelog cita um
`voices.example.json` (`CHANGELOG.md:19`), mas **esse arquivo não existe no
repositório** — só `voices.json` (conferido com `ls`; erro `No such file`).
Ou o exemplo nunca foi commitado ou foi removido: **não verificado** qual caso.

## 7. `SUPPORT.md` — suporte

**Propósito:** orientar onde pedir ajuda (`SUPPORT.md:1-5`).

| Linha(s) | Conteúdo |
|---|---|
| `SUPPORT.md:7-17` | Comunitário e gratuito: abrir Issue no GitHub (`github.com/samucamg/multivozes_br_engine/issues`) para bugs reprodutíveis e sugestões |
| `SUPPORT.md:21-33` | Pago: dúvidas de instalação/código, depuração, consultoria e features personalizadas via `samtutor.online/store/suporte-e-instalacao` |

## O que não foi verificado (limites desta unidade)

- Nenhum comando dos guias foi executado (instalação, `curl`, n8n, systemd,
  Docker) — proibido neste despacho; eficácia dos procedimentos: **não verificada**.
- Correspondência parâmetro a parâmetro entre `API_USAGE_GUIDE.md` e o código
  (`main.py`/`tts_handler.py`) — cruzar com `main.md` e `tts-handler.md`.
- Correspondência entre as tabelas de vozes (`VOICES.md`/`N8N-INTEGRATION.md`)
  e o `voices.json` efetivo — cruzar com `texto-config-utils.md`.
- Links externos (YouTube, multivozes.com, n8n, Keep a Changelog): **não
  verificados** (sem chamadas de rede).
- Destino do `voices.example.json` citado no changelog e ausente no disco.

# Aplicação `multivozes_br_engine` — visão geral

API de texto-para-fala (TTS) auto-hospedada, compatível com a API da OpenAI,
que converte texto em áudio usando as vozes neurais gratuitas do Microsoft Edge
(`edge-tts`). O ponto de entrada é `main.py` (FastAPI + Uvicorn); a síntese e a
conversão de formato vivem em `tts_handler.py`; a limpeza de texto, os padrões
e as constantes vivem em `handle_text.py`, `config.py`, `utils.py` e
`voices.json`. O empacotamento e a operação estão documentados a partir de
`Dockerfile`, `multivozes_br_engine.service`, `.env.example`,
`requirements.txt` e `.github/workflows/publish.yml`. Os guias já existentes
na raiz do repositório estão inventariados à parte.

## Arquitetura (em poucas linhas)

- `main.py` expõe `POST /v1/audio/speech` e `GET /v1/models`, valida o corpo da
  requisição com Pydantic e exige Bearer Token quando `REQUIRE_API_KEY=true`.
- `handle_text.preparar_texto_para_tts` limpa o texto (emojis, Markdown, HTML)
  antes da síntese, salvo quando `REMOVE_FILTER=true`.
- `tts_handler.gerar_audio` resolve apelido de voz via `voices.json`, converte
  `speed` em taxa do `edge-tts`, sintetiza MP3 e, se preciso, converte o formato
  ou concatena silêncios de `[pause: ...]` com `pydub` (+ `ffmpeg`).
- O áudio temporário é devolvido como `FileResponse` e removido em seguida via
  `BackgroundTasks` (`os.unlink`).
- Configuração via variáveis de ambiente (`.env`, modelo em `.env.example`);
  deploy via Docker ou systemd; CI publica a imagem no Docker Hub.

## Fluxo de uma requisição `POST /v1/audio/speech`

1. Autenticação: com `REQUIRE_API_KEY=false`, `verificar_chave_api`
   retorna sem checar a chave e a rota passa **sem** o cabeçalho
   `Authorization` (corrigido na Fase 2). Com a exigência ligada, envie
   `Authorization: Bearer <API_KEY>` (401 com `WWW-Authenticate: Bearer` se
   ausente, com esquema diferente de Bearer ou se inválida; 500 se
   a exigência está ativa mas `API_KEY` não foi definida — verificado antes
   mesmo do cabeçalho).
2. Validação: `input` vazio gera 400; `speed` é validado pelo Pydantic
   (`0.25–2.0`; fora da faixa retorna 422).
3. Se `REMOVE_FILTER` for falso, aplica `preparar_texto_para_tts`.
4. Resolve voz (`voice` ou `VOZ_PADRAO`), formato (`response_format`, MIME via
   `TIPOS_MIME_AUDIO`) e velocidade.
5. `gerar_audio`: apelido → voz Edge TTS → `speed` → taxa (`+N%`) → `edge-tts`
   (MP3) → opcional `pydub` (conversão de formato ou pausas) → caminho do
   arquivo temporário.
6. Devolve o `FileResponse` (`filename=speech.<formato>`) e agenda o
   `os.unlink` do temporário. Qualquer exceção vira HTTP 500.

## Índice

- [Unidade `main` — `main.py`: rotas, autenticação e inicialização](main.md)
- [Unidade `tts-handler` — `tts_handler.py`: síntese, pausas e conversão](tts-handler.md)
- [Unidade `texto-config-utils` — `handle_text.py`, `config.py`, `utils.py`, `voices.json`](texto-config-utils.md)
- [Unidade `deploy` — `Dockerfile`, systemd, `.env.example`, dependências e CI](deploy.md)
- [Unidade `docs-existentes` — inventário dos guias da raiz](docs-existentes.md)

## Variáveis de ambiente (tabela única)

| Variável | Padrão | Onde é lida | Realmente usada? |
|---|---|---|---|
| `PORT` | `5050` | `main.py` (`PORTA`) | Sim — porta do Uvicorn; valor não inteiro ou fora de 1–65535 aborta a inicialização com `RuntimeError("Configuração inválida: PORT='...'")`. |
| `DEFAULT_VOICE` | `pt-BR-ThalitaMultilingualNeural` | `main.py` (`VOZ_PADRAO`) | Sim — usada quando `voice` é omitido. |
| `DEFAULT_RESPONSE_FORMAT` | `mp3` | `main.py` (`FORMATO_RESPOSTA_PADRAO`) | Sim — usada quando `response_format` é omitido (corrigido na Fase 2); valor fora de `TIPOS_MIME_AUDIO` aborta a inicialização. |
| `DEFAULT_SPEED` | `1.0` | `main.py` (`VELOCIDADE_PADRAO`) | Sim — usada quando `speed` é omitido (corrigido na Fase 2); valor não numérico ou fora de 0.25–2.0 aborta a inicialização. |
| `REMOVE_FILTER` | `False` | `main.py` via `obter_env_bool` | Sim — `True` desativa `preparar_texto_para_tts`. |
| `API_KEY` | `None` | `utils.py:14` (`CHAVE_API`) | Sim — comparada com o Bearer Token quando `REQUIRE_API_KEY=true`. |
| `REQUIRE_API_KEY` | `True` | `utils.py:15` (`EXIGIR_CHAVE_API`) | Sim — `False` faz `verificar_chave_api` retornar sem checar e a rota passa sem `Authorization` (corrigido na Fase 2). |
| `DETAILED_ERROR_LOGGING` | `True` | `utils.py:16` (`LOG_ERROS_DETALHADO`) | Sim — controla impressão de tracebacks no console. |
| `PROXY` | `None` | `tts_handler.py:16` | Sim — repassado a `edge_tts.Communicate`; `None` = sem proxy. |

Conversão de booleanos (`obter_env_bool`, `utils.py:8-11`): `True` se o valor
(lowercase) estiver em `("yes", "y", "true", "1", "t")`; qualquer outra coisa
(incluindo `"0"`, `"false"`, `"no"`, `"off"`) é `False`.

## Lacunas conhecidas e discrepâncias

Tudo abaixo foi marcado como **"não verificado"** pelas unidades ou é
divergência **verificada por leitura do código/disco** nesta consolidação.
Nada aqui foi executado (servidor, rede e instalação eram proibidos no
despacho).

1. ~~**`speed` entre 2.0 e 4.0 gera HTTP 500**~~ — **corrigido na Fase 2**:
   o modelo Pydantic aceita `0.25–2.0` e valores fora da faixa retornam 422.
2. ~~**`DEFAULT_RESPONSE_FORMAT` e `DEFAULT_SPEED` lidas mas sem uso efetivo**~~
   — **corrigido na Fase 2**: passaram a valer como padrão quando o campo é
   omitido na requisição.
3. ~~**variável de idioma padrão sem uso no código**~~ — **corrigido na Fase 2**:
   removida de `config.py` e do `.env.example` (nenhum `.py` a lia).
4. ~~**flag de compatibilidade só existente no `.env.example`**~~ — **corrigido na Fase 2**:
   removida do `.env.example` (nenhum `.py` a lia).
5. **`voices.example.json` citado no `CHANGELOG.md:19` mas ausente do disco**
   (verificado com `ls`: só existe `voices.json`; se o exemplo nunca foi
   commitado ou foi removido, não se sabe).
6. **`README.md` duplicado** (verificado por leitura): o bloco
   "▶️ Executando o Servidor" + "Opção 1" aparece duas vezes seguidas
   (`README.md:133-145`).
7. **Serviço systemd divergente** (verificado por leitura): a "Opção 3" do
   `README.md:193-238` (serviço `multivozes`, `/opt/multivozes_br_engine`,
   `RestartSec=5`) difere de `multivozes_br_engine.service` (nome
   `multivozes_br_engine`, `/opt/tts`, `RestartSec=10`). Qual usar em produção:
   **não verificado**.
8. **Python 3.8+ vs 3.11** (verificado por leitura): o pré-requisito diz
   Python 3.8+ (`README.md:95`) mas a imagem usa `python:3.11-slim`
   (`Dockerfile:1`) — compatibilidade com 3.8: **não verificada**.
9. **Tabelas de vozes divergentes** (verificado por leitura): `VOICES.md:9-21`
   e `N8N-INTEGRATION.md:39-53` trazem um mapeamento (ex.:
   `alloy`→`en-US-AndrewMultilingualNeural`) diferente do `voices.json` efetivo
   (ex.: `alloy`→`pt-BR-ThalitaMultilingualNeural`). Qual está vigente em
   produção: **não verificado**.
10. Presença do `ffmpeg` no ambiente e formatos além de `mp3` **não testados**;
    nenhum comando de deploy, instalação, `curl`, n8n ou systemd foi executado.
    (O comportamento sem cabeçalho `Authorization` foi verificado por teste do
    orquestrador em ambiente descartável — ver item 14.)
11. **Ordem das transformações em `handle_text.py`** (imagem Markdown vs regra
    de link; bloco de código vs remoção de símbolos): comportamento confirmado
    só por leitura, **não verificado** com execução.
12. **Links externos** (YouTube, multivozes.com, n8n, Keep a Changelog):
    **não verificados** (sem chamadas de rede).
13. **Correções de citação feitas nesta consolidação** (linhas que apontavam
    para fora do arquivo ou com desvio verificado): em `tts-handler.md`,
    `tts_handler.py:175` → `:170` (o arquivo tem 170 linhas, última sem quebra
    final), `162-172` → `158-170`, `164-167` → `160-163`, `125-169` → `125-170`,
    regex de pausas `74` → `71`, `Communicate/save` `143-144` → `138-139`,
    traceback de segmento `91-92` → `87-88`, `unlink` de segmento `87` → `85`,
    `AudioSegment.silent` `101` → `102`.
14. ~~**`REQUIRE_API_KEY=false` ainda exige o cabeçalho `Authorization`**~~ —
    **corrigido na Fase 2**: `security = HTTPBearer(auto_error=False)`, então
    sem cabeçalho (ou com esquema diferente de Bearer) a requisição chega a
    `verificar_chave_api`, que retorna sem checar quando a exigência está
    desligada. Medido: com `REQUIRE_API_KEY=false`,
    `POST /v1/audio/speech` sem cabeçalho → HTTP 200. Com a exigência ligada,
    sem cabeçalho/esquema errado/chave errada → HTTP 401 com
    `WWW-Authenticate: Bearer` — ver `main.md` (seções da rota, de
    `verificar_chave_api` e "Como executar e testar").

## O que esta consolidação fez e não fez

- Fez: criou este `README.md`, padronizou o vocabulário para pt-BR nos 5
  arquivos (só prosa; nomes de código, comandos, caminhos e citações literais
  preservados) e conferiu por amostragem (`grep`/`sed -n`/`awk`) que todas as
  citações `arquivo:linha` apontam para linhas existentes.
- Não fez: nenhuma nova pesquisa de fontes, nenhuma execução (servidor, rede,
  instalação), nenhuma alteração em código, nos `.md` da raiz, no `.estrutura/`
  ou no contract.

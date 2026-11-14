# Unidade `main` — `main.py`

## Propósito

`main.py` é o ponto de entrada da aplicação: cria a aplicação FastAPI, define o
modelo de requisição, as duas rotas da API compatível com OpenAI
(`POST /v1/audio/speech` e `GET /v1/models`), a dependência de autenticação por
chave de API e o bloco de inicialização do servidor Uvicorn.

## Rotas

### `POST /v1/audio/speech` — `text_to_speech` (`main.py:89-122`)

Gera áudio a partir de texto e devolve o arquivo de áudio.

- **Parâmetros (corpo JSON, modelo `TTSRequest`, `main.py:21-28`):**
  - `input: str` (obrigatório) — texto a converter. Texto vazio gera
    `HTTPException 400` (`main.py:95-97`).
  - `model: str = "tts-1"` — nome do modelo (aceito mas não altera o
    comportamento de síntese; só é listado em `/v1/models`).
  - `voice: str | None = None` — apelido OpenAI (ex.: `alloy`) ou nome técnico
    Edge TTS (ex.: `pt-BR-ThalitaMultilingualNeural`). Se omitido, usa
    `VOZ_PADRAO` (`main.py:41`).
  - `response_format: str | None = None` — formato do áudio de saída. Quando
    omitido, vale `FORMATO_RESPOSTA_PADRAO` (`DEFAULT_RESPONSE_FORMAT`).
  - `speed: float | None = None`, validado pelo Pydantic com `ge=0.25, le=2.0`
    (`main.py:28`). Valores fora de `0.25–2.0` são rejeitados com HTTP 422.
    Quando omitido, vale `VELOCIDADE_PADRAO` (`DEFAULT_SPEED`).
- **Autenticação:** dependência `verificar_chave_api` (definida em
  `main.py`, chamada na rota). Com `REQUIRE_API_KEY=false` a rota passa sem
  o cabeçalho `Authorization` (corrigido na Fase 2 — ver seção
  "Autenticação — `verificar_chave_api`" abaixo).
- **Fluxo interno:**
  1. Se `REMOVER_FILTRO` for falso, aplica `preparar_texto_para_tts(texto)`
     (`main.py:100-101`).
  2. Resolve voz/formato/velocidade e o MIME via
     `TIPOS_MIME_AUDIO.get(formato_resposta, "audio/mpeg")` (`main.py:104-107`) —
     formato desconhecido cai no padrão `audio/mpeg`, mas o sufixo do arquivo
     continua sendo o formato pedido.
  3. Chama `await gerar_audio(texto, voz, formato_resposta, velocidade)`
     (`main.py:110`).
  4. Agenda a remoção do arquivo temporário com
     `background_tasks.add_task(os.unlink, caminho_ficheiro_audio)` (`main.py:113`)
     e devolve `FileResponse` com `filename=f"speech.{formato_resposta}"`
     (`main.py:115`).
- **Retorno:** arquivo de áudio (`FileResponse`) com o `media_type`
  correspondente.
- **Erros:**
  - `400` — campo `input` vazio/ausente (corrigido na Fase 2: o
    `HTTPException` da validação não é mais reempacotado como 500).
  - `401` — com a exigência ativa: cabeçalho `Authorization` ausente, esquema
    diferente de Bearer ou chave inválida (todos com o cabeçalho
    `WWW-Authenticate: Bearer`).
  - `422` — `speed` fora de `0.25–2.0` (validação do Pydantic).
  - `500` — `CHAVE_API` não configurada quando a exigência está ativa
    (verificado antes mesmo do cabeçalho); qualquer exceção em `gerar_audio`
    vira `HTTPException 500 "Erro interno no servidor: ..."`.
    Detalhe do traceback só é impresso no console quando
    `LOG_ERROS_DETALHADO` é verdadeiro.

### `GET /v1/models` — `listar_modelos` (`main.py:126-131`)

- Função **síncrona** (`def`, não `async`).
- **Sem autenticação** (não usa `verificar_chave_api`).
- **Retorno:** `{"data": [{"id": ..., "object": "model"}]}` montado a partir de
  `DADOS_MODELOS` de `tts_handler.py` (atualmente `tts-1` e `tts-1-hd`).

## Autenticação — `verificar_chave_api`

Dependência FastAPI baseada em `HTTPBearer(auto_error=False)`:

- Se `EXIGIR_CHAVE_API` for falso, `verificar_chave_api` retorna sem checar
  e a rota passa **sem** o cabeçalho `Authorization` (corrigido na Fase 2:
  antes, `HTTPBearer()` com `auto_error=True` rejeitava a requisição com
  403/401 antes de a função ser chamada).
- Se a exigência está ativa mas `CHAVE_API` está vazia/não definida → HTTP 500
  (verificado primeiro, mesmo sem cabeçalho).
- Se `credentials is None` (cabeçalho ausente **ou** esquema diferente de
  Bearer, que o `HTTPBearer` com `auto_error=False` também devolve como
  `None`) → HTTP 401 com `WWW-Authenticate: Bearer`.
- Se `credentials.credentials != CHAVE_API` → HTTP 401 com
  `WWW-Authenticate: Bearer`.
- Caso válido, retorna a credencial.

## Variáveis de ambiente e valores padrão

Lidas em `main.py:34-52` (com `load_dotenv()` em `main.py:31`):

| Variável | Padrão (`config.py`) | Observação |
|---|---|---|
| `PORT` | `5050` | Convertido com `int(...)`; valor não inteiro ou fora de 1–65535 aborta a inicialização com `RuntimeError("Configuração inválida: PORT='...'")`. |
| `DEFAULT_VOICE` | `pt-BR-ThalitaMultilingualNeural` | Voz usada quando `voice` é omitido. |
| `DEFAULT_RESPONSE_FORMAT` | `mp3` | Lida em `FORMATO_RESPOSTA_PADRAO` e usada quando `response_format` é omitido; valor fora de `TIPOS_MIME_AUDIO` aborta a inicialização com `RuntimeError("Configuração inválida: DEFAULT_RESPONSE_FORMAT='...'")` (corrigido na Fase 2). |
| `DEFAULT_SPEED` | `1.0` | Lida em `VELOCIDADE_PADRAO` e usada quando `speed` é omitido; valor não numérico ou fora de 0.25–2.0 aborta a inicialização com `RuntimeError("Configuração inválida: DEFAULT_SPEED='...'")` (corrigido na Fase 2). |
| `REMOVE_FILTER` | `False` | Booleano via `obter_env_bool`; `True` desativa `preparar_texto_para_tts`. |

Autenticação e logging vêm de `utils.py`: `API_KEY` (padrão `None`),
`REQUIRE_API_KEY` (padrão `True`), `DETAILED_ERROR_LOGGING` (padrão `True`).

## Dependências (imports de `main.py:1-16`)

- `fastapi`, `pydantic`, `python-dotenv`, `uvicorn` (servidor, usado em
  `main.py:146`).
- Módulos locais: `config.DEFAULT_CONFIGS`, `handle_text.preparar_texto_para_tts`,
  `tts_handler.gerar_audio` e `tts_handler.DADOS_MODELOS`,
  `utils.obter_env_bool`, `utils.TIPOS_MIME_AUDIO`, `utils.LOG_ERROS_DETALHADO`,
  `utils.EXIGIR_CHAVE_API`, `utils.CHAVE_API`. (`Request` não é mais
  importado do FastAPI desde a Fase 2.)

## Como executar e testar

- Executar: `python main.py` — sobe Uvicorn em `0.0.0.0:$PORT`
  (`main.py:135-146`; banner informativo impresso antes).
- Teste manual (sem checagem de chave, com `REQUIRE_API_KEY=false`):
  `POST http://localhost:5050/v1/audio/speech` com JSON
  `{"input": "Olá", "voice": "pt-BR-ThalitaMultilingualNeural"}` **sem**
  cabeçalho `Authorization` (corrigido na Fase 2 — o cabeçalho era exigido
  por bug em `HTTPBearer()` mesmo com a checagem desligada);
  verificar que a resposta é áudio e que o arquivo temporário foi removido
  após o envio.
- Teste de autenticação: com `REQUIRE_API_KEY=true` e `API_KEY=xxx`, chamar sem
  cabeçalho, com esquema `Basic` ou com chave errada retorna 401 (com
  `WWW-Authenticate: Bearer`); com a chave correta deve gerar áudio.
  Com `REQUIRE_API_KEY=false`, sem cabeçalho → 200.

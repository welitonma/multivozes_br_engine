# Unidade `main` — `main.py`

## Propósito

`main.py` é o ponto de entrada da aplicação: cria a aplicação FastAPI, define o
modelo de requisição, as duas rotas da API compatível com OpenAI
(`POST /v1/audio/speech` e `GET /v1/models`), a dependência de autenticação por
chave de API e o bloco de inicialização do servidor Uvicorn.

## Rotas

### `POST /v1/audio/speech` — `text_to_speech` (`main.py:66-99`)

Gera áudio a partir de texto e devolve o arquivo de áudio.

- **Parâmetros (corpo JSON, modelo `TTSRequest`, `main.py:21-28`):**
  - `input: str` (obrigatório) — texto a converter. Texto vazio gera
    `HTTPException 400` (`main.py:71-73`).
  - `model: str = "tts-1"` — nome do modelo (aceito mas não altera o
    comportamento de síntese; só é listado em `/v1/models`).
  - `voice: str | None = None` — apelido OpenAI (ex.: `alloy`) ou nome técnico
    Edge TTS (ex.: `pt-BR-ThalitaMultilingualNeural`). Se omitido, usa
    `VOZ_PADRAO` (`main.py:81`).
  - `response_format: str = "mp3"` — formato do áudio de saída.
  - `speed: float = 1.0`, validado pelo Pydantic com `ge=0.25, le=4.0`
    (`main.py:28`). **Atenção:** `velocidade_para_taxa` em `tts_handler.py:42-47`
    rejeita valores fora de `0.25–2.0` com `ValueError`, que cai no `except`
    genérico e vira HTTP 500. Ou seja, `speed` entre 2.0 e 4.0 passa na
    validação do modelo mas falha na geração (erro 500).
- **Autenticação:** dependência `verificar_chave_api` (`main.py:66`,
  definida em `main.py:42-63`). **Bug conhecido:** sem o cabeçalho
  `Authorization`, `HTTPBearer()` (`main.py:18`) rejeita a requisição antes
  de a função ser chamada (ver seção "Autenticação — `verificar_chave_api`"
  abaixo).
- **Fluxo interno:**
  1. Se `REMOVER_FILTRO` for falso, aplica `preparar_texto_para_tts(texto)`
     (`main.py:75-77`).
  2. Resolve voz/formato/velocidade e o MIME via
     `TIPOS_MIME_AUDIO.get(formato_resposta, "audio/mpeg")` (`main.py:81-85`) —
     formato desconhecido cai no padrão `audio/mpeg`, mas o sufixo do arquivo
     continua sendo o formato pedido.
  3. Chama `await gerar_audio(texto, voz, formato_resposta, velocidade)`
     (`main.py:88`).
  4. Agenda a remoção do arquivo temporário com
     `background_tasks.add_task(os.unlink, caminho_ficheiro_audio)` (`main.py:91`)
     e devolve `FileResponse` com `filename=f"speech.{formato_resposta}"`
     (`main.py:93`).
- **Retorno:** arquivo de áudio (`FileResponse`) com o `media_type`
  correspondente.
- **Erros:**
  - `400` — campo `input` vazio/ausente.
  - `403` — cabeçalho `Authorization` ausente (rejeitado por `HTTPBearer()`
    em `main.py:18` antes de `verificar_chave_api`; em FastAPI/Starlette mais
    novos o código é `401`). Vale mesmo com `REQUIRE_API_KEY=false` (bug
    conhecido, ainda não corrigido no código).
  - `401` — chave de API inválida (via dependência, com a exigência ativa).
  - `500` — `CHAVE_API` não configurada quando a exigência está ativa; qualquer
    exceção em `gerar_audio` (incluindo `speed > 2.0`) vira
    `HTTPException 500 "Erro interno no servidor: ..."` (`main.py:95-99`).
    Detalhe do traceback só é impresso no console quando
    `LOG_ERROS_DETALHADO` é verdadeiro (`main.py:96-98`).

### `GET /v1/models` — `listar_modelos` (`main.py:102-108`)

- Função **síncrona** (`def`, não `async`).
- **Sem autenticação** (não usa `verificar_chave_api`).
- **Retorno:** `{"data": [{"id": ..., "object": "model"}]}` montado a partir de
  `DADOS_MODELOS` de `tts_handler.py` (atualmente `tts-1` e `tts-1-hd`).

## Autenticação — `verificar_chave_api` (`main.py:42-63`)

Dependência FastAPI baseada em `HTTPBearer()` (`main.py:18`):

- Se `EXIGIR_CHAVE_API` for falso, `verificar_chave_api` retorna sem checar
  (`main.py:48-49`). **Bug conhecido (não corrigido no código):** na prática a
  requisição sem cabeçalho `Authorization` nunca chega até essa função,
  porque `HTTPBearer()` usa `auto_error=True` por padrão e o FastAPI rejeita
  a requisição antes — HTTP 403 nas versões fixadas do `requirements.txt`,
  HTTP 401 em FastAPI/Starlette mais novos (verificado por teste do
  orquestrador em ambiente descartável). Ou seja, mesmo com
  `REQUIRE_API_KEY=false` é preciso enviar `Authorization: Bearer
  <qualquer-valor>` para alcançar a rota.
- Se a exigência está ativa mas `CHAVE_API` está vazia/não definida → HTTP 500
  (`main.py:51-56`).
- Se `credentials.credentials != CHAVE_API` → HTTP 401 (`main.py:58-62`).
- Caso válido, retorna a credencial (`main.py:63`).

## Variáveis de ambiente e valores padrão

Lidas em `main.py:34-38` (com `load_dotenv()` em `main.py:31`):

| Variável | Padrão (`config.py`) | Observação |
|---|---|---|
| `PORT` | `5050` | Convertido com `int(...)`; valor inválido quebra na inicialização (`ValueError` não tratado). |
| `DEFAULT_VOICE` | `pt-BR-ThalitaMultilingualNeural` | Voz usada quando `voice` é omitido. |
| `DEFAULT_RESPONSE_FORMAT` | `mp3` | Lida em `FORMATO_RESPOSTA_PADRAO`, mas **não é usada** em `text_to_speech` — o formato efetivo vem sempre de `request_data.response_format` (padrão `mp3` do modelo). |
| `DEFAULT_SPEED` | `1.0` | Lida em `VELOCIDADE_PADRAO`, mas **não é usada** — a velocidade efetiva vem sempre de `request_data.speed` (padrão `1.0`). |
| `REMOVE_FILTER` | `False` | Booleano via `obter_env_bool`; `True` desativa `preparar_texto_para_tts`. |

Autenticação e logging vêm de `utils.py`: `API_KEY` (padrão `None`),
`REQUIRE_API_KEY` (padrão `True`), `DETAILED_ERROR_LOGGING` (padrão `True`).

## Dependências (imports de `main.py:1-16`)

- `fastapi`, `pydantic`, `python-dotenv`, `uvicorn` (servidor, usado em
  `main.py:122`).
- Módulos locais: `config.DEFAULT_CONFIGS`, `handle_text.preparar_texto_para_tts`,
  `tts_handler.gerar_audio` e `tts_handler.DADOS_MODELOS`,
  `utils.obter_env_bool`, `utils.TIPOS_MIME_AUDIO`, `utils.LOG_ERROS_DETALHADO`,
  `utils.EXIGIR_CHAVE_API`, `utils.CHAVE_API`.

## Como executar e testar

- Executar: `python main.py` — sobe Uvicorn em `0.0.0.0:$PORT`
  (`main.py:111-122`; banner informativo impresso antes).
- Teste manual (sem checagem de chave, com `REQUIRE_API_KEY=false`):
  `POST http://localhost:5050/v1/audio/speech` com JSON
  `{"input": "Olá", "voice": "pt-BR-ThalitaMultilingualNeural"}` **e um
  cabeçalho `Authorization: Bearer <qualquer-valor>`** (exigido por bug
  conhecido em `HTTPBearer()`, `main.py:18`, mesmo com a checagem desligada);
  verificar que a resposta é áudio e que o arquivo temporário foi removido
  após o envio.
- Teste de autenticação: com `REQUIRE_API_KEY=true` e `API_KEY=xxx`, chamar sem
  cabeçalho `Authorization: Bearer xxx` deve retornar erro (403 nas versões
  fixadas do `requirements.txt`; 401 em FastAPI/Starlette mais novos); com a
  chave correta deve gerar áudio. Comportamento sem cabeçalho **verificado por
  teste do orquestrador em ambiente descartável, versões fixadas** (sem
  cabeçalho → 403; com qualquer `Bearer x` e `REQUIRE_API_KEY=false` → 200).

# Unidade `tts-handler` — `tts_handler.py`

## Propósito

`tts_handler.py` concentra a síntese de voz: converte o parâmetro `speed` para o
formato de taxa do `edge-tts`, resolve apelidos de voz via `voices.json`, gera o
áudio (com ou sem pausas customizadas `[pause: ...]`) e converte o formato com
`pydub`. É chamado por `main.py:88` via `gerar_audio`.

## Funções

### `carregar_mapeamento_vozes()` (`tts_handler.py:21-32`)

- Lê `voices.json` no mesmo diretório do arquivo (`Path(__file__).parent /
  "voices.json"`, `tts_handler.py:23`).
- Se o arquivo **não existir**, imprime aviso e devolve um mapeamento padrão
  com apenas 2 entradas (`alloy`, `echo`) (`tts_handler.py:24-31`). **Atenção:**
  se o arquivo existir mas contiver JSON inválido, `json.load` levanta exceção
  **na importação do módulo** (linha 34 executa no import) e a aplicação nem
  inicia — não há `try/except` para esse caso.
- Resultado carregado uma única vez em `MAPEAMENTO_VOZES` (`tts_handler.py:34`).

### `velocidade_para_taxa(velocidade: float) -> str` (`tts_handler.py:42-47`)

- Converte multiplicador em taxa do edge-tts: `percentagem = int((v - 1) * 100)`;
  devolve `"+N%"` se `>= 0`, senão `"N%"` (ex.: `1.5 → "+50%"`, `0.5 → "-50%"`).
- **Validação:** levanta `ValueError("A velocidade deve estar entre 0.25 e 2.0.")`
  fora de `0.25–2.0` (`tts_handler.py:44-45`). Como `main.py` aceita até `4.0`
  no modelo Pydantic, valores `2.0 < speed <= 4.0` resultam em HTTP 500.

### `gerar_audio(texto, voz, formato_resposta, velocidade) -> str` (`tts_handler.py:49-61`)

- **Parâmetros:** `texto: str`, `voz: str` (apelido ou nome técnico),
  `formato_resposta: str`, `velocidade: float`. **Retorno:** caminho do arquivo
  temporário de áudio gerado.
- Resolve a voz: `MAPEAMENTO_VOZES.get(voz, voz)` — apelido desconhecido é
  passado adiante como nome técnico Edge TTS (`tts_handler.py:55`).
- Calcula `taxa` via `velocidade_para_taxa` (`tts_handler.py:56`).
- Desvia para `gerar_audio_com_pausas` se o texto contiver `[pause:` (busca
  case-insensitive via `texto.lower()`, `tts_handler.py:59`); senão chama
  `gerar_audio_normal` (`tts_handler.py:62`).

### `gerar_audio_com_pausas(texto, voz, taxa, formato) -> str` (`tts_handler.py:64-122`)

- **Sintaxe de pausa:** `[pause: 2s]` ou `[pause: 500ms]` (decimais aceitos:
  `\d+(\.\d+)?`, unidades `s|ms`, case-insensitive — regex em
  `tts_handler.py:71`). Cada `[pause: ...]` vira silêncio digital inserido via
  `pydub`.
- **Fluxo:**
  1. Divide o texto com `re.split` capturando tempo e unidade (`tts_handler.py:71`).
  2. Para cada parte de texto não vazia, gera MP3 via `gerar_audio_normal(...,
     'mp3')`, carrega com `AudioSegment.from_mp3` e concatena (`tts_handler.py:82-89`).
  3. Converte a pausa para ms (`s × 1000`), limitada a **10 000 ms por pausa**
     (`tts_handler.py:98`), e adiciona `AudioSegment.silent(duration=pausa_ms,
     frame_rate=24000)` (`tts_handler.py:102`).
  4. Exporta o resultado no formato pedido com
     `audio_final.export(caminho_final, format=formato.lower())`
     (`tts_handler.py:111`). Falha na exportação remove o arquivo parcial e
     levanta `RuntimeError("Falha ao exportar áudio com pausas: ...")`
     (`tts_handler.py:112-119`).
- **Erros:** falha num segmento levanta
  `RuntimeError("Falha ao gerar segmento de áudio: ...")` com causa encadeada
  (`tts_handler.py:90-94`) — **não devolve áudio parcial**. Detalhe do
  traceback só é impresso se `LOG_ERROS_DETALHADO` (`tts_handler.py:87-88`).
- **Arquivos temporários:** segmentos intermediários são removidos após
  concatenar (`tts_handler.py:85`); o arquivo final (prefixo aleatório via
  `tempfile.NamedTemporaryFile(delete=False, ...)`, `tts_handler.py:105-107`) é
  devolvido ao chamador — a remoção cabe ao `BackgroundTasks` em `main.py:91`.
- **Observação:** texto **sem nenhuma parte falável** (só pausas) gera um
  arquivo só de silêncio; texto `None`/não-string não é tratado aqui (o filtro
  em `main.py` garante string quando ativo).

### `gerar_audio_normal(texto, voz, taxa, formato) -> str` (`tts_handler.py:125-170`)

- **Fluxo:**
  1. Cria MP3 temporário (`tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")`,
     `tts_handler.py:131-134`).
  2. `edge_tts.Communicate(texto, voz, rate=taxa, proxy=PROXY)` e
     `await comunicador.save(caminho_temp_mp3)` (`tts_handler.py:138-139`).
  3. Se `formato.lower() != "mp3"`: carrega com `AudioSegment.from_mp3` e
     exporta no formato pedido em novo temporário, removendo o MP3
     intermediário (`tts_handler.py:147-157`). Se for `mp3`, o temporário já é
     o final (`tts_handler.py:158-160`).
- **Erros:** qualquer exceção remove os temporários existentes e levanta
  `RuntimeError("Falha ao gerar ou converter áudio: ...")`
  (`tts_handler.py:158-170`, limpeza em `tts_handler.py:160-163`).
- **Retorno:** caminho do arquivo final (`tts_handler.py:170`).

## Constantes e dados

- `PROXY = os.getenv("PROXY", None)` (`tts_handler.py:16`) — repassado ao
  `edge_tts.Communicate`; `None` = sem proxy. Carregado com `load_dotenv()` em
  `tts_handler.py:12`.
- `DADOS_MODELOS` (`tts_handler.py:37-40`): `tts-1` e `tts-1-hd`, expostos por
  `GET /v1/models`.

## Fluxo de dados (resumo)

`texto/voz/formato/speed` (main) → apelido→voz Edge TTS → `speed`→taxa
(`+N%`) → `edge-tts` (MP3) → opcional `pydub` (conversão de formato ou
concatenação com silêncios) → caminho temporário → `FileResponse` → `os.unlink`.

## Variáveis de ambiente e dependências

- **Ambiente:** `PROXY` (padrão `None`). `LOG_ERROS_DETALHADO` (de `utils.py`)
  controla a impressão de tracebacks.
- **Dependências:** `edge-tts` (síntese, chamada de rede aos servidores Edge),
  `pydub` (conversão/concatenação — exige **ffmpeg** instalado no sistema para
  `export`/`from_mp3`, embora o código não mencione isso), `python-dotenv`.
  **Não verificado:** presença de ffmpeg no ambiente e formatos além de `mp3`
  suportados pelo `export` local — não testado neste despacho (nenhum áudio foi
  gerado, conforme limites da tarefa).

## Como executar e testar

- Indireto, via API: `POST /v1/audio/speech` (ver `docs/aplicacao/main.md`).
- Teste de pausas: `{"input": "Olá [pause: 2s] mundo", ...}` deve devolver áudio
  com ~2 s de silêncio no meio; `[pause: 500ms]` similar em milissegundos.
- Teste de voz: `{"voice": "alloy"}` deve soar igual a
  `pt-BR-ThalitaMultilingualNeural` (mapeamento em `voices.json`).
- Teste de erro: `speed: 3.0` passa na validação do modelo mas deve retornar
  HTTP 500 (limite `2.0` de `velocidade_para_taxa`).

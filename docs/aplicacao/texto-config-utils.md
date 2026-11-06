# Unidade `texto-config-utils` — `handle_text.py`, `config.py`, `utils.py`, `voices.json`

## 1. `handle_text.py` — limpeza de texto

### Propósito

`preparar_texto_para_tts` remove do texto tudo que o motor de voz não deve
pronunciar (emojis, Markdown, HTML) antes da síntese. É chamada em
`main.py:77` quando `REMOVE_FILTER` é falso.

### Função `preparar_texto_para_tts(texto: str) -> str` (`handle_text.py:4-48`)

- **Parâmetro:** `texto: str`. **Retorno:** texto limpo (`str`).
- Entrada não-string devolve `""` (`handle_text.py:14-15`).
- **Ordem das transformações** (relevante porque a ordem importa):
  1. `emoji.replace_emoji(texto, replace='')` — remove emojis (`handle_text.py:19`).
  2. Links Markdown `[texto](url)` → `texto` (`handle_text.py:23`).
  3. Imagens Markdown `![alt](src)` → `alt` (`handle_text.py:25`). **Nota:**
     aplicada **depois** da regra de links, então `![alt](src)` casa primeiro
     com a regra de links? Na prática, o `!` inicial permanece e o resto vira
     `alt` — comportamento confirmado só por leitura do código; **não
     verificado** com execução.
  4. Símbolos `**`, `__`, `*`, `_`, `~~` removidos, conteúdo mantido
     (`handle_text.py:27`).
  5. Blocos de código ` ```...``` ` removidos por inteiro, regex não-gulosa com
     `[\s\S]` (`handle_text.py:29`). **Nota:** como vem **depois** da remoção de
     símbolos, crases dentro do bloco já foram removidas antes — o bloco ainda
     é detectado pelo ` ``` ` restante? **Não verificado** com execução.
  6. Código inline `` `x` `` → `x` (`handle_text.py:31`).
  7. Cabeçalhos `### Título` → `Título` (multiline, `handle_text.py:33`).
  8. Tags HTML `</?[^>]+(>|$)` removidas (`handle_text.py:35`).
  9. Normalização: `\n{2,}` → `\n\n`, ` {2,}` → ` `, `strip()`
     (`handle_text.py:39-44`).
- **Dependência:** biblioteca `emoji` (`handle_text.py:2`).

## 2. `config.py` — padrões

### Propósito

`DEFAULT_CONFIGS` (`config.py:1-13`) centraliza os valores padrão usados quando
a variável de ambiente correspondente não existe. Não lê ambiente — só declara
o dicionário; a leitura está em `main.py:34-38` e `utils.py:14-16`.

### Valores

| Chave | Valor | Consumidor |
|---|---|---|
| `PORT` | `5050` | `main.py:34` (`int(os.getenv(...))`) |
| `API_KEY` | `None` | `utils.py:14` |
| `DEFAULT_VOICE` | `pt-BR-ThalitaMultilingualNeural` | `main.py:35` |
| `DEFAULT_RESPONSE_FORMAT` | `mp3` | `main.py:36` (lido mas **sem uso efetivo** — ver `main.md`) |
| `DEFAULT_SPEED` | `1.0` | `main.py:37` (lido mas **sem uso efetivo** — ver `main.md`) |
| `DEFAULT_LANGUAGE` | `pt-BR` | **Sem uso no código** (nenhuma referência fora daqui — confirmado por busca). |
| `REQUIRE_API_KEY` | `True` | `utils.py:15` |
| `REMOVE_FILTER` | `False` | `main.py:38` |
| `DETAILED_ERROR_LOGGING` | `True` | `utils.py:16` |

## 3. `utils.py` — ambiente e constantes

### Propósito

Carrega `.env` (`utils.py:5`), converte flags booleanas e expõe as constantes de
autenticação, logging e MIME usadas por `main.py` e `tts_handler.py`.

### `obter_env_bool(nome_variavel, valor_padrao=False) -> bool` (`utils.py:8-11`)

- Lê `os.getenv(nome_variavel, str(valor_padrao))` e devolve `True` se o valor
  (lowercase) estiver em `("yes", "y", "true", "1", "t")`; qualquer outra coisa
  (incluindo `"0"`, `"false"`, `"no"`, `"off"`) é `False`.
- **Detalhe:** o padrão é convertido com `str(...)` antes da comparação, então
  `True` → `"True"` → `"true"` → `True`; `False` → `"False"` → `False`. Correto.

### Constantes (`utils.py:14-27`)

- `CHAVE_API = os.getenv('API_KEY', DEFAULT_CONFIGS.get("API_KEY"))`
  (`utils.py:14`) — `None` se ausente.
- `EXIGIR_CHAVE_API = obter_env_bool('REQUIRE_API_KEY', True)` (`utils.py:15`).
- `LOG_ERROS_DETALHADO = obter_env_bool('DETAILED_ERROR_LOGGING', True)`
  (`utils.py:16`).
- `TIPOS_MIME_AUDIO` (`utils.py:19-27`):
  `mp3→audio/mpeg`, `opus→audio/opus`, `aac→audio/aac`, `flac→audio/flac`,
  `wav→audio/wav`, `pcm→audio/L16`.

### Variáveis de ambiente (resumo das três fontes)

`PORT`, `DEFAULT_VOICE`, `DEFAULT_RESPONSE_FORMAT`, `DEFAULT_SPEED`,
`REMOVE_FILTER` (lidas em `main.py`), `API_KEY`, `REQUIRE_API_KEY`,
`DETAILED_ERROR_LOGGING` (lidas em `utils.py`), `PROXY` (lida em
`tts_handler.py`). Ver `.env.example` para o modelo — **nenhum arquivo `.env`
foi lido nem criado neste despacho**.

## 4. `voices.json` — apelidos de voz

### Propósito

Mapa estático apelido OpenAI → voz Edge TTS, carregado por
`carregar_mapeamento_vozes` (`tts_handler.py:21-32`). Permite usar nomes como
`alloy`/`nova` na API e obter vozes reais.

### Conteúdo (12 entradas)

| Apelido | Voz Edge TTS |
|---|---|
| `alloy` | `pt-BR-ThalitaMultilingualNeural` |
| `ash` | `en-US-AndrewMultilingualNeural` |
| `ballad` | `en-US-BrianMultilingualNeural` |
| `cedar` | `en-AU-WilliamMultilingualNeural` |
| `coral` | `en-US-AvaMultilingualNeural` |
| `echo` | `it-IT-GiuseppeMultilingualNeural` |
| `fable` | `en-US-EmmaMultilingualNeural` |
| `onyx` | `fr-FR-RemyMultilingualNeural` |
| `nova` | `de-DE-SeraphinaMultilingualNeural` |
| `sage` | `fr-FR-VivienneMultilingualNeural` |
| `shimmer` | `de-DE-FlorianMultilingualNeural` |
| `verse` | `ko-KR-HyunsuMultilingualNeural` |

**Nota:** só `alloy` aponta para voz `pt-BR`; as demais apontam para vozes
`en-US/en-AU/it-IT/fr-FR/de-DE/ko-KR`. Nomes não listados passam direto como
nome técnico (`MAPEAMENTO_VOZES.get(voz, voz)`).

## Como executar e testar

- Filtro de texto: `python3 -c "from handle_text import preparar_texto_para_tts; print(preparar_texto_para_tts('Olá **mundo** 🌍'))"` deve imprimir
  `Olá mundo`. **Não verificado:** não executado neste despacho (apenas leitura).
- Booleanos: `REQUIRE_API_KEY=false/0/no/off` → `False`;
  `true/1/yes/y/t` (qualquer caixa) → `True`.
- Vozes: trocar um valor em `voices.json` e reiniciar altera a voz do apelido
  sem mexer no código; remover o arquivo ativa o fallback de 2 vozes com
  aviso no console.

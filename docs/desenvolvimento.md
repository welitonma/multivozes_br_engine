# Desenvolvimento

Guia para montar o ambiente de desenvolvimento do Multivozes BR Engine.

## Python 3.11 obrigatório

O projeto usa **Python 3.11**, o mesmo da imagem Docker (`python:3.11-slim`).
O motivo: o `pydantic==2.7.1` fixado no `requirements.txt` depende do
`pydantic-core==2.18.2`, que não publica wheel para Python 3.13+ — no Python
3.14 do sistema a instalação não resolve. A atualização do Python está
prevista só para a Fase 5; até lá, use sempre o 3.11.

## Montando o ambiente

O `python3.11` não está no PATH desta máquina (só o 3.14), então use o
`uv` — ele baixa o interpretador 3.11 automaticamente se faltar:

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
```

Não documentamos `python3.11 -m venv` como alternativa porque o
interpretador 3.11 não vem instalado nesta máquina.

## Rodando as ferramentas

```bash
.venv/bin/ruff check .   # lint (regras E9 + F; baseline explícita no pyproject.toml)
.venv/bin/pytest -q        # testes (testpaths = ["tests"])
```

## O que os testes cobrem

- `tests/test_handle_text.py`: limpeza de texto (`preparar_texto_para_tts`).
- `tests/test_utils.py`: leitura de booleanos de ambiente e tipos MIME.
- `tests/test_tts_handler.py`: conversão de velocidade e roteamento da síntese.
- `tests/test_api.py`: rotas `GET /v1/models` e `POST /v1/audio/speech` via `TestClient`.

## `xfail` estrito

Os bugs conhecidos entram como `pytest.mark.xfail(strict=True)`: o teste
descreve o comportamento CORRETO e hoje falha de propósito. Quando o bug for
corrigido (Fase 2), o teste passa e o `xfail` estrito quebra (`xpassed`),
forçando remover a marca. A suíte exige `0 xpassed`.

## Rede bloqueada nos testes

Uma fixture `autouse` em `tests/conftest.py` troca `socket.socket.connect`
por uma função que levanta `AssertionError`. Nenhum teste chama o `edge-tts`
real: a síntese é sempre simulada (`monkeypatch` em `main.gerar_audio`).

## Como adicionar um teste

1. Crie ou edite `tests/test_*.py` (o pytest coleta por esse padrão).
2. Se o teste precisa de outra configuração, use
   `monkeypatch.setattr(main, "NOME", valor)` — trocar `os.environ` depois
do `import main` não tem efeito (a configuração é lida na importação).
3. Para a rota de áudio, use as fixtures `client` e `audio_falso` do
   `conftest.py`.

## Custo medido

Venv de 3.11 com app + pytest + httpx + ruff ocupa cerca de **85 MB** em
disco; o `import main` usa cerca de **217 MB** de RAM (medido em 2026-11-06).

## FFmpeg

O `ffmpeg` é necessário para a conversão de formato de áudio (`pydub`).
Sem ele, a síntese até gera áudio, mas a conversão para `mp3`/`opus`/`flac`
falha. No Docker ele já vem instalado (`Dockerfile`); no host, instale pelo
gerenciador de pacotes (ex.: `sudo apt install ffmpeg`).

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
.venv/bin/pytest         # testes (testpaths = ["tests"]; os testes chegam na Fase 1)
```

## Custo medido

Venv de 3.11 com app + pytest + httpx + ruff ocupa cerca de **85 MB** em
disco; o `import main` usa cerca de **217 MB** de RAM (medido em 2026-11-06).

## FFmpeg

O `ffmpeg` é necessário para a conversão de formato de áudio (`pydub`).
Sem ele, a síntese até gera áudio, mas a conversão para `mp3`/`opus`/`flac`
falha. No Docker ele já vem instalado (`Dockerfile`); no host, instale pelo
gerenciador de pacotes (ex.: `sudo apt install ffmpeg`).

"""Configuração comum dos testes de caracterização (Fase 1)."""

import os

# Forçado (não setdefault): os testes não dependem de .env nem do ambiente
# do desenvolvedor (load_dotenv não sobrescreve variável já definida).
os.environ["REQUIRE_API_KEY"] = "false"
os.environ["API_KEY"] = "teste"
os.environ["DETAILED_ERROR_LOGGING"] = "false"
os.environ["REMOVE_FILTER"] = "false"
os.environ["DEFAULT_VOICE"] = "pt-BR-ThalitaMultilingualNeural"

import socket
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main
import tts_handler


@pytest.fixture(autouse=True)
def _rede_bloqueada(monkeypatch):
    """Bloqueia rede: nada pode chamar o edge-tts real nos testes."""

    def _sem_rede(self, *args, **kwargs):
        raise AssertionError("rede bloqueada nos testes")

    monkeypatch.setattr(socket.socket, "connect", _sem_rede)


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def audio_falso(monkeypatch):
    """Troca main.gerar_audio por corrotina que registra args, replica a
    checagem de velocidade do gerar_audio real e grava um .mp3 temporário."""
    chamadas = []
    caminhos = []

    async def _falso(texto, voz, formato, velocidade):
        chamadas.append((texto, voz, formato, velocidade))
        # Igual ao gerar_audio real: valida primeiro, para que speed fora
        # de 0.25-2.0 levante ValueError e a rota devolva o mesmo 500.
        tts_handler.velocidade_para_taxa(velocidade)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(b"ID3\x00\x01")
            caminhos.append(f.name)
        return caminhos[-1]

    monkeypatch.setattr(main, "gerar_audio", _falso)
    return {"chamadas": chamadas, "caminhos": caminhos}

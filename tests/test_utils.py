"""Caracterização de utils.obter_env_bool e TIPOS_MIME_AUDIO."""

import os

import pytest

from utils import TIPOS_MIME_AUDIO, obter_env_bool


@pytest.mark.parametrize("valor", ["yes", "y", "true", "1", "t", "Y", "TRUE", "Yes", "TrUe"])
def test_obter_env_bool_verdadeiros(monkeypatch, valor):
    monkeypatch.setenv("FEATURE002_PROBE", valor)
    assert obter_env_bool("FEATURE002_PROBE", False) is True


@pytest.mark.parametrize("valor", ["0", "false", "no", "off", "", "False", "NO", "qualquer"])
def test_obter_env_bool_falsos(monkeypatch, valor):
    monkeypatch.setenv("FEATURE002_PROBE", valor)
    assert obter_env_bool("FEATURE002_PROBE", True) is False


def test_obter_env_bool_ausente_usa_padrao(monkeypatch):
    monkeypatch.delenv("FEATURE002_AUSENTE", raising=False)
    assert obter_env_bool("FEATURE002_AUSENTE", True) is True
    assert obter_env_bool("FEATURE002_AUSENTE", False) is False


def test_obter_env_bool_ignora_variavel_nao_definida(monkeypatch):
    monkeypatch.delenv("FEATURE002_AUSENTE", raising=False)
    assert obter_env_bool("FEATURE002_AUSENTE") is False


def test_tipos_mime_audio():
    assert TIPOS_MIME_AUDIO == {
        "mp3": "audio/mpeg",
        "opus": "audio/opus",
        "aac": "audio/aac",
        "flac": "audio/flac",
        "wav": "audio/wav",
        "pcm": "audio/L16",
    }

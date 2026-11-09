"""Caracterização de tts_handler (comportamento atual)."""

import asyncio
import inspect
import json
from pathlib import Path

import pytest

import tts_handler
from tts_handler import gerar_audio, velocidade_para_taxa


@pytest.mark.parametrize(
    ("velocidade", "taxa"),
    [(0.25, "-75%"), (1.0, "+0%"), (1.5, "+50%"), (2.0, "+100%")],
)
def test_velocidade_para_taxa_validos(velocidade, taxa):
    assert velocidade_para_taxa(velocidade) == taxa


@pytest.mark.parametrize("velocidade", [0.24, 2.01])
def test_velocidade_para_taxa_invalidos(velocidade):
    with pytest.raises(ValueError):
        velocidade_para_taxa(velocidade)


def test_gerar_audio_e_corrotinas():
    assert inspect.iscoroutinefunction(gerar_audio)
    assert inspect.iscoroutinefunction(tts_handler.gerar_audio_normal)
    assert inspect.iscoroutinefunction(tts_handler.gerar_audio_com_pausas)


def test_gerar_audio_traduz_apelido(monkeypatch):
    chamadas = {}

    async def normal_falso(texto, voz, taxa, formato):
        chamadas["normal"] = (texto, voz, taxa, formato)
        return "/tmp/x.mp3"

    async def pausas_falso(texto, voz, taxa, formato):
        chamadas["pausas"] = (texto, voz, taxa, formato)
        return "/tmp/y.mp3"

    monkeypatch.setattr(tts_handler, "gerar_audio_normal", normal_falso)
    monkeypatch.setattr(tts_handler, "gerar_audio_com_pausas", pausas_falso)
    assert asyncio.run(gerar_audio("olá", "alloy", "mp3", 1.0)) == "/tmp/x.mp3"
    assert chamadas["normal"] == ("olá", "pt-BR-ThalitaMultilingualNeural", "+0%", "mp3")


def test_gerar_audio_voz_desconhecida_passa_direto(monkeypatch):
    chamadas = {}

    async def normal_falso(texto, voz, taxa, formato):
        chamadas["normal"] = (texto, voz, taxa, formato)
        return "/tmp/x.mp3"

    async def pausas_falso(texto, voz, taxa, formato):
        chamadas["pausas"] = (texto, voz, taxa, formato)
        return "/tmp/y.mp3"

    monkeypatch.setattr(tts_handler, "gerar_audio_normal", normal_falso)
    monkeypatch.setattr(tts_handler, "gerar_audio_com_pausas", pausas_falso)
    asyncio.run(gerar_audio("olá", "voz-desconhecida-X", "mp3", 1.0))
    assert chamadas["normal"][1] == "voz-desconhecida-X"


def test_gerar_audio_com_pausa_vai_para_pausas(monkeypatch):
    chamadas = {}

    async def normal_falso(texto, voz, taxa, formato):
        chamadas["normal"] = (texto, voz, taxa, formato)
        return "/tmp/x.mp3"

    async def pausas_falso(texto, voz, taxa, formato):
        chamadas["pausas"] = (texto, voz, taxa, formato)
        return "/tmp/y.mp3"

    monkeypatch.setattr(tts_handler, "gerar_audio_normal", normal_falso)
    monkeypatch.setattr(tts_handler, "gerar_audio_com_pausas", pausas_falso)
    assert asyncio.run(gerar_audio("oi [pause: 1s] fim", "alloy", "mp3", 1.0)) == "/tmp/y.mp3"
    assert "pausas" in chamadas


def test_gerar_audio_com_pausa_qualquer_caixa(monkeypatch):
    chamadas = {}

    async def normal_falso(texto, voz, taxa, formato):
        chamadas["normal"] = (texto, voz, taxa, formato)
        return "/tmp/x.mp3"

    async def pausas_falso(texto, voz, taxa, formato):
        chamadas["pausas"] = (texto, voz, taxa, formato)
        return "/tmp/y.mp3"

    monkeypatch.setattr(tts_handler, "gerar_audio_normal", normal_falso)
    monkeypatch.setattr(tts_handler, "gerar_audio_com_pausas", pausas_falso)
    asyncio.run(gerar_audio("oi [PAUSE: 500ms] fim", "alloy", "mp3", 1.0))
    assert "pausas" in chamadas
    assert "normal" not in chamadas


def test_gerar_audio_sem_pausa_vai_para_normal(monkeypatch):
    chamadas = {}

    async def normal_falso(texto, voz, taxa, formato):
        chamadas["normal"] = (texto, voz, taxa, formato)
        return "/tmp/x.mp3"

    async def pausas_falso(texto, voz, taxa, formato):
        chamadas["pausas"] = (texto, voz, taxa, formato)
        return "/tmp/y.mp3"

    monkeypatch.setattr(tts_handler, "gerar_audio_normal", normal_falso)
    monkeypatch.setattr(tts_handler, "gerar_audio_com_pausas", pausas_falso)
    asyncio.run(gerar_audio("olá mundo", "alloy", "mp3", 1.0))
    assert "normal" in chamadas
    assert "pausas" not in chamadas


def test_voices_json_tem_alloy():
    dados = json.loads((Path(tts_handler.__file__).parent / "voices.json").read_text(encoding="utf-8"))
    assert dados["alloy"] == "pt-BR-ThalitaMultilingualNeural"

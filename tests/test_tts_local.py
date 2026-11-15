"""Backend local Piper em CPU (FEATURE-004).

Sem rede, sem modelo real, sem .env: o módulo `piper` é sempre um dublê
(`monkeypatch` em `sys.modules`) com a mesma forma da API real
(`PiperVoice`/`PiperConfig`/`SynthesisConfig`/`AudioChunk`, sessão
onnxruntime com `sess_options` e `providers`).
"""

import asyncio
import importlib.util
import json
import os
import runpy
import sys
import types
from pathlib import Path

import pytest
from pydub import AudioSegment

import tts_handler
from tts_backends import piper as modulo_piper
from tts_backends.piper import BackendPiper

TAXA_VOZ_FALSA = 22050
SEGUNDOS_POR_SEGMENTO = 0.5


def _modelo_real_disponivel():
    """Só o teste de integração real usa pacote/modelo de verdade."""
    if importlib.util.find_spec("piper") is None:
        return False
    return (
        Path(os.getenv("PIPER_MODELS_DIR", "./models"))
        / "pt_BR-faber-medium.onnx"
    ).exists()


@pytest.fixture(autouse=True)
def _ambiente_limpo(monkeypatch):
    """Isola os testes de .env e do ambiente do desenvolvedor."""
    monkeypatch.delenv("TTS_BACKEND", raising=False)
    monkeypatch.delenv("PIPER_MODELS_DIR", raising=False)
    monkeypatch.delenv("PIPER_THREADS", raising=False)


@pytest.fixture
def piper_falso(monkeypatch, tmp_path):
    """Instala o dublê do `piper` + `onnxruntime` e um modelo falso em disco."""
    modulo_piper._CACHE_VOZES.clear()
    gravador = {"chamadas": [], "sessoes": []}

    class SynthesisConfig:
        def __init__(self, length_scale=None):
            self.length_scale = length_scale

    class PiperConfig:
        @staticmethod
        def from_dict(d):
            return types.SimpleNamespace(sample_rate=d["audio"]["sample_rate"])

    class VozFalsa:
        def synthesize(self, texto, syn_config=None):
            escala = syn_config.length_scale if syn_config is not None else None
            gravador["chamadas"].append((texto, escala))
            n = int(TAXA_VOZ_FALSA * SEGUNDOS_POR_SEGMENTO)
            pcm = b"\x00\x00" * n
            yield types.SimpleNamespace(
                sample_rate=TAXA_VOZ_FALSA, audio_int16_bytes=pcm
            )

    class PiperVoice:
        def __init__(self, config=None, session=None, espeak_data_dir=None,
                     download_dir=None):
            self.config = config
            self.session = session

        def synthesize(self, texto, syn_config=None):
            return VozFalsa().synthesize(texto, syn_config)

    class SessionOptions:
        def __init__(self):
            self.intra_op_num_threads = 0

    class InferenceSession:
        def __init__(self, *args, **kwargs):
            gravador["sessoes"].append((args, kwargs))

    mod_piper = types.ModuleType("piper")
    mod_voice = types.ModuleType("piper.voice")
    mod_voice.SynthesisConfig = SynthesisConfig
    mod_voice.PiperConfig = PiperConfig
    mod_voice.PiperVoice = PiperVoice
    mod_piper.voice = mod_voice
    mod_espeak = types.ModuleType("piper.phonemize_espeak")
    mod_espeak.ESPEAK_DATA_DIR = tmp_path / "espeak-ng-data"
    mod_ort = types.ModuleType("onnxruntime")
    mod_ort.SessionOptions = SessionOptions
    mod_ort.InferenceSession = InferenceSession
    monkeypatch.setitem(sys.modules, "piper", mod_piper)
    monkeypatch.setitem(sys.modules, "piper.voice", mod_voice)
    monkeypatch.setitem(sys.modules, "piper.phonemize_espeak", mod_espeak)
    monkeypatch.setitem(sys.modules, "onnxruntime", mod_ort)

    monkeypatch.setenv("PIPER_MODELS_DIR", str(tmp_path))
    (tmp_path / "pt_BR-faber-medium.onnx").write_bytes(b"falso-onnx")
    (tmp_path / "pt_BR-faber-medium.onnx.json").write_text(
        json.dumps(
            {
                "num_symbols": 10,
                "num_speakers": 1,
                "audio": {"sample_rate": TAXA_VOZ_FALSA},
                "espeak": {"voice": "pt-br"},
                "phoneme_id_map": {},
            }
        ),
        encoding="utf-8",
    )
    return gravador


def test_piper_nao_importado_sem_uso():
    assert "piper" not in sys.modules


def test_padrao_sem_env_usa_edge(monkeypatch):
    chamadas = {}

    async def normal_falso(texto, voz, taxa, formato):
        chamadas["normal"] = (texto, voz, taxa, formato)
        return "/tmp/x.mp3"

    async def pausas_falso(texto, voz, taxa, formato):
        chamadas["pausas"] = (texto, voz, taxa, formato)
        return "/tmp/y.mp3"

    monkeypatch.setattr(tts_handler, "gerar_audio_normal", normal_falso)
    monkeypatch.setattr(tts_handler, "gerar_audio_com_pausas", pausas_falso)
    caminho = asyncio.run(tts_handler.gerar_audio("olá", "alloy", "mp3", 1.0))
    assert caminho == "/tmp/x.mp3"
    assert chamadas["normal"][1] == "pt-BR-ThalitaMultilingualNeural"


def test_env_edge_explicito_usa_edge(monkeypatch):
    monkeypatch.setenv("TTS_BACKEND", "edge")
    assert tts_handler.obter_backend_nome() == "edge"

    async def normal_falso(texto, voz, taxa, formato):
        return "/tmp/x.mp3"

    monkeypatch.setattr(tts_handler, "gerar_audio_normal", normal_falso)
    assert (
        asyncio.run(tts_handler.gerar_audio("olá", "alloy", "mp3", 1.0))
        == "/tmp/x.mp3"
    )


def test_backend_invalido_erro_claro(monkeypatch):
    monkeypatch.setenv("TTS_BACKEND", "Xyz")
    with pytest.raises(RuntimeError, match=r"Configuração inválida: TTS_BACKEND='Xyz'"):
        asyncio.run(tts_handler.gerar_audio("olá", "alloy", "mp3", 1.0))


@pytest.mark.parametrize(
    "apelido",
    ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
)
def test_piper_resolve_apelidos(apelido):
    modelo = BackendPiper().resolver_voz(apelido)
    assert modelo.startswith("pt_BR-")


def test_piper_voz_desconhecida_passa_direto():
    assert BackendPiper().resolver_voz("pt_BR-faber-medium") == "pt_BR-faber-medium"
    assert BackendPiper().resolver_voz("modelo-x") == "modelo-x"


def test_piper_sintetiza_wav(piper_falso, tmp_path):
    backend = BackendPiper()
    caminho = asyncio.run(backend.sintetizar_wav("olá mundo", "alloy", 1.0))
    assert Path(caminho).exists()
    audio = AudioSegment.from_wav(caminho)
    assert audio.frame_rate == TAXA_VOZ_FALSA
    assert abs(len(audio) - SEGUNDOS_POR_SEGMENTO * 1000) < 50
    Path(caminho).unlink()
    (texto, escala) = piper_falso["chamadas"][0]
    assert texto == "olá mundo"
    assert escala == 1.0


@pytest.mark.parametrize(
    ("velocidade", "escala"),
    [(0.5, 2.0), (1.0, 1.0), (2.0, 0.5)],
)
def test_piper_length_scale_por_velocidade(piper_falso, velocidade, escala):
    backend = BackendPiper()
    caminho = asyncio.run(backend.sintetizar_wav("oi", "alloy", velocidade))
    Path(caminho).unlink()
    assert piper_falso["chamadas"][0][1] == pytest.approx(escala)


def test_piper_threads_na_sessao(piper_falso, monkeypatch):
    monkeypatch.setenv("PIPER_THREADS", "2")
    caminho = asyncio.run(BackendPiper().sintetizar_wav("oi", "alloy", 1.0))
    Path(caminho).unlink()
    (args, kwargs) = piper_falso["sessoes"][0]
    assert kwargs["providers"] == ["CPUExecutionProvider"]
    assert kwargs["sess_options"].intra_op_num_threads == 2
    assert str(args[0]).endswith("pt_BR-faber-medium.onnx")


def test_piper_modelo_ausente_erro_claro(monkeypatch, tmp_path):
    monkeypatch.setenv("PIPER_MODELS_DIR", str(tmp_path))
    with pytest.raises(RuntimeError, match=r"não encontrado.*baixar_voz_piper\.py"):
        asyncio.run(BackendPiper().sintetizar_wav("oi", "voz-inexistente-y", 1.0))


def test_piper_sem_pacote_erro_claro(piper_falso, monkeypatch):
    for nome in ("piper", "piper.voice", "piper.phonemize_espeak", "onnxruntime"):
        monkeypatch.setitem(sys.modules, nome, None)
    with pytest.raises(RuntimeError, match="piper-tts"):
        asyncio.run(BackendPiper().sintetizar_wav("oi", "alloy", 1.0))


def test_piper_velocidade_invalida(piper_falso):
    with pytest.raises(ValueError, match="entre 0.25 e 2.0"):
        asyncio.run(BackendPiper().sintetizar_wav("oi", "alloy", 3.0))


def test_piper_pausas_duracao_total(piper_falso, monkeypatch):
    monkeypatch.setenv("TTS_BACKEND", "piper")
    caminho = asyncio.run(
        tts_handler.gerar_audio("fala [pause: 1s] fim", "alloy", "wav", 1.0)
    )
    audio = AudioSegment.from_wav(caminho)
    esperado_ms = SEGUNDOS_POR_SEGMENTO * 1000 * 2 + 1000
    assert abs(len(audio) - esperado_ms) < 120
    assert audio.frame_rate == TAXA_VOZ_FALSA
    Path(caminho).unlink()


@pytest.mark.parametrize(
    ("formato", "formato_leitura"), [("mp3", "mp3"), ("wav", "wav"), ("opus", "ogg")]
)
def test_piper_formatos(piper_falso, monkeypatch, formato, formato_leitura):
    monkeypatch.setenv("TTS_BACKEND", "piper")
    caminho = asyncio.run(tts_handler.gerar_audio("olá", "alloy", formato, 1.0))
    assert Path(caminho).suffix == f".{formato}"
    audio = AudioSegment.from_file(caminho, format=formato_leitura)
    assert len(audio) > 0
    Path(caminho).unlink()


def test_script_baixar_voz_chama_downloader(monkeypatch, tmp_path, capsys):
    chamadas = {}

    def download_voice(voz, download_dir, force_redownload=False):
        chamadas["voz"] = voz
        chamadas["destino"] = Path(download_dir)
        (Path(download_dir) / f"{voz}.onnx").write_bytes(b"falso")

    mod_dl = types.ModuleType("piper.download_voices")
    mod_dl.download_voice = download_voice
    monkeypatch.setitem(sys.modules, "piper.download_voices", mod_dl)
    monkeypatch.setattr(
        sys, "argv", ["baixar_voz_piper.py", "pt_BR-faber-medium", "--dir", str(tmp_path)]
    )
    ns = runpy.run_path("scripts/baixar_voz_piper.py", run_name="__teste__")
    assert ns["main"]() == 0
    assert chamadas == {"voz": "pt_BR-faber-medium", "destino": tmp_path}
    assert (tmp_path / "pt_BR-faber-medium.onnx").exists()
    assert "OK" in capsys.readouterr().out


@pytest.mark.skipif(
    not _modelo_real_disponivel(),
    reason="sem pacote piper-tts ou modelo pt_BR-faber-medium em disco",
)
def test_integracao_piper_real(monkeypatch):
    monkeypatch.setenv("TTS_BACKEND", "piper")
    caminho = asyncio.run(
        tts_handler.gerar_audio("Olá, teste de voz local.", "alloy", "wav", 1.0)
    )
    try:
        audio = AudioSegment.from_wav(caminho)
        assert len(audio) > 0
    finally:
        Path(caminho).unlink(missing_ok=True)

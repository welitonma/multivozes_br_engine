"""Backend Piper local (CPU, sem rede em runtime).

O pacote `piper` (piper-tts) só é importado dentro das funções, nunca no topo
do módulo — assim `import tts_handler` funciona mesmo sem o piper-tts
instalado. O modelo (.onnx + .onnx.json) é carregado sob demanda e guardado
num cache em memória, um por voz.
"""

import asyncio
import json
import os
import tempfile
import wave
from pathlib import Path

_CACHE_VOZES = {}


def diretorio_modelos() -> Path:
    """Diretório dos modelos (.onnx): `PIPER_MODELS_DIR` ou `./models`."""
    return Path(os.getenv("PIPER_MODELS_DIR", "./models"))


def num_threads() -> int:
    """Threads do onnxruntime: `PIPER_THREADS` ou todos os núcleos."""
    try:
        bruto = os.getenv("PIPER_THREADS", "").strip()
        return max(1, int(bruto) if bruto else (os.cpu_count() or 1))
    except ValueError:
        return os.cpu_count() or 1


def carregar_mapeamento_piper():
    """Apelidos OpenAI -> modelo Piper pt-BR (`voices_piper.json`)."""
    caminho = Path(__file__).resolve().parent.parent / "voices_piper.json"
    if not caminho.exists():
        return {}
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def _verificar_arquivos(modelo: str, caminho_modelo: Path) -> Path:
    """Garante que .onnx + .onnx.json existem (antes de importar `piper`)."""
    caminho_config = Path(str(caminho_modelo) + ".json")
    if not caminho_modelo.exists() or not caminho_config.exists():
        raise RuntimeError(
            f"Modelo Piper '{modelo}' não encontrado em '{caminho_modelo}'. "
            f"Esperados '{caminho_modelo}' e '{caminho_config}'. "
            f"Baixe com: python scripts/baixar_voz_piper.py {modelo} "
            f"(destino: PIPER_MODELS_DIR ou ./models). "
            f"Dependência: pip install -r requirements-local.txt"
        )
    return caminho_config


def _carregar_voz(modelo: str, caminho_modelo: Path, threads: int):
    """Abre o .onnx com sessão CPU dedicada (espelha `PiperVoice.load`)."""
    caminho_config = _verificar_arquivos(modelo, caminho_modelo)
    # Import preguiçoso: este módulo pode ser importado sem piper-tts.
    try:
        from piper.phonemize_espeak import ESPEAK_DATA_DIR
        from piper.voice import PiperConfig, PiperVoice

        import onnxruntime
    except ImportError:
        raise RuntimeError(
            "Pacote 'piper-tts' não instalado. "
            "Rode: pip install -r requirements-local.txt"
        )
    with open(caminho_config, "r", encoding="utf-8") as f:
        config = PiperConfig.from_dict(json.load(f))
    opcoes = onnxruntime.SessionOptions()
    opcoes.intra_op_num_threads = threads
    sessao = onnxruntime.InferenceSession(
        str(caminho_modelo),
        sess_options=opcoes,
        providers=["CPUExecutionProvider"],
    )
    return PiperVoice(
        config=config,
        session=sessao,
        espeak_data_dir=ESPEAK_DATA_DIR,
        download_dir=Path.cwd(),
    )


class BackendPiper:
    """Síntese offline em CPU via Piper (onnxruntime, só CPU)."""

    def __init__(self):
        self._mapa = carregar_mapeamento_piper()

    def resolver_voz(self, nome: str) -> str:
        """Apelido OpenAI -> modelo Piper; nome desconhecido passa direto."""
        return self._mapa.get(nome, nome)

    def caminho_modelo(self, modelo: str) -> Path:
        """Caminho esperado do .onnx para o modelo."""
        return diretorio_modelos() / f"{modelo}.onnx"

    def obter_voz(self, modelo: str):
        """Devolve a voz em cache (carrega o .onnx na primeira vez)."""
        chave = str(self.caminho_modelo(modelo))
        if chave not in _CACHE_VOZES:
            _CACHE_VOZES[chave] = _carregar_voz(modelo, Path(chave), num_threads())
        return _CACHE_VOZES[chave]

    async def sintetizar_wav(self, texto: str, voz: str, velocidade: float) -> str:
        """Sintetiza o texto e devolve o caminho de um WAV temporário."""
        if not 0.25 <= velocidade <= 2.0:
            raise ValueError("A velocidade deve estar entre 0.25 e 2.0.")
        modelo = self.resolver_voz(voz)
        escala = 1.0 / velocidade
        _verificar_arquivos(modelo, self.caminho_modelo(modelo))

        def _sintetizar():
            try:
                from piper.voice import SynthesisConfig
            except ImportError:
                raise RuntimeError(
                    "Pacote 'piper-tts' não instalado. "
                    "Rode: pip install -r requirements-local.txt"
                )

            voz_obj = self.obter_voz(modelo)
            blocos = list(
                voz_obj.synthesize(texto, syn_config=SynthesisConfig(length_scale=escala))
            )
            if not blocos:
                raise RuntimeError(
                    f"O modelo Piper '{modelo}' não gerou áudio para o texto informado."
                )
            taxa = blocos[0].sample_rate
            pcm = b"".join(b.audio_int16_bytes for b in blocos)
            ficheiro = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            caminho = ficheiro.name
            ficheiro.close()
            with wave.open(caminho, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(taxa)
                w.writeframes(pcm)
            return caminho

        return await asyncio.to_thread(_sintetizar)

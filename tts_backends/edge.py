"""Backend Edge (online): a chamada original ao edge-tts, sem mudar comportamento.

O `tts_handler.gerar_audio_normal` delega para `BackendEdge.gerar`, então o
caminho padrão (`TTS_BACKEND=edge` ou ausente) gera exatamente o mesmo áudio.
"""

import json
import os
import tempfile
import traceback
from pathlib import Path

import edge_tts
from pydub import AudioSegment

from utils import LOG_ERROS_DETALHADO

PROXY = os.getenv("PROXY", None)


def carregar_mapeamento_edge():
    """Carrega o mapeamento de apelidos OpenAI para vozes Edge (`voices.json`)."""
    caminho_ficheiro = Path(__file__).resolve().parent.parent / "voices.json"
    if not caminho_ficheiro.exists():
        print("AVISO: Ficheiro 'voices.json' não encontrado. A usar mapeamento padrão.")
        return {
            "alloy": "pt-BR-FranciscaNeural",
            "echo": "pt-BR-AntonioNeural",
        }
    with open(caminho_ficheiro, "r", encoding="utf-8") as f:
        return json.load(f)


class BackendEdge:
    """Síntese online via edge-tts (comportamento original do projeto)."""

    def __init__(self):
        self._mapa = carregar_mapeamento_edge()

    def resolver_voz(self, nome: str) -> str:
        """Apelido OpenAI -> voz Edge; nome desconhecido passa direto."""
        return self._mapa.get(nome, nome)

    async def gerar(self, texto: str, voz: str, taxa: str, formato: str) -> str:
        """Gera áudio com edge-tts (MP3 intermediário + conversão)."""
        ficheiro_temp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        caminho_temp_mp3 = ficheiro_temp_mp3.name
        ficheiro_temp_mp3.close()

        caminho_final_audio = None

        try:
            comunicador = edge_tts.Communicate(texto, voz, rate=taxa, proxy=PROXY)
            await comunicador.save(caminho_temp_mp3)

            if formato.lower() != "mp3":
                ficheiro_temp_final = tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{formato}"
                )
                caminho_final_audio = ficheiro_temp_final.name
                ficheiro_temp_final.close()

                audio = AudioSegment.from_mp3(caminho_temp_mp3)
                audio.export(caminho_final_audio, format=formato.lower())

                Path(caminho_temp_mp3).unlink()
            else:
                caminho_final_audio = caminho_temp_mp3

        except Exception as e:
            if caminho_temp_mp3 and Path(caminho_temp_mp3).exists():
                Path(caminho_temp_mp3).unlink(missing_ok=True)
            if caminho_final_audio and Path(caminho_final_audio).exists():
                Path(caminho_final_audio).unlink(missing_ok=True)

            if LOG_ERROS_DETALHADO:
                print(f"Erro detalhado em gerar_audio: {traceback.format_exc()}")
            raise RuntimeError(f"Falha ao gerar ou converter áudio: {e}")

        return caminho_final_audio

    async def sintetizar_wav(self, texto: str, voz: str, velocidade: float) -> str:
        """Sintetiza e devolve um WAV temporário (interface `BackendTTS`)."""
        # Import preguiçoso aqui para evitar import circular na importação
        # (tts_handler importa este módulo no topo).
        from tts_handler import velocidade_para_taxa

        taxa = velocidade_para_taxa(velocidade)
        return await self.gerar(texto, self.resolver_voz(voz), taxa, "wav")

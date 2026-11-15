"""Interface comum dos backends de TTS (FEATURE-004)."""

from typing import Protocol


class BackendTTS(Protocol):
    """Contrato que todo backend de voz precisa cumprir."""

    async def sintetizar_wav(self, texto: str, voz: str, velocidade: float) -> str:
        """Sintetiza o texto e devolve o caminho de um WAV temporário."""
        ...

    def resolver_voz(self, nome: str) -> str:
        """Resolve apelido OpenAI (ou devolve o nome como modelo)."""
        ...

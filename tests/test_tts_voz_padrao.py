"""Voz padrão do Piper (FEATURE-006).

Sem rede, sem modelo real, sem .env: só `resolver_voz`/`voz_padrao`
(que nunca importam o `piper`).
"""

import pytest

from tts_backends import piper as modulo_piper
from tts_backends.piper import BackendPiper


@pytest.fixture(autouse=True)
def _ambiente_limpo(monkeypatch):
    """Isola os testes do ambiente do desenvolvedor."""
    monkeypatch.delenv("PIPER_DEFAULT_VOICE", raising=False)


def test_resolver_voz_edge_cai_na_faber():
    assert (
        BackendPiper().resolver_voz("pt-BR-ThalitaMultilingualNeural")
        == "pt_BR-faber-medium"
    )


@pytest.mark.parametrize("nome", ["", "   "])
def test_resolver_voz_vazia_cai_na_faber(nome):
    assert BackendPiper().resolver_voz(nome) == "pt_BR-faber-medium"


@pytest.mark.parametrize(
    "apelido",
    ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
)
def test_resolver_apelido_usa_mapa(apelido):
    assert BackendPiper().resolver_voz(apelido) == "pt_BR-faber-medium"


@pytest.mark.parametrize(
    "modelo", ["pt_BR-faber-medium", "pt_BR-cadu-medium", "modelo-x"]
)
def test_resolver_modelo_passa_direto(modelo):
    assert BackendPiper().resolver_voz(modelo) == modelo


def test_piper_default_voice_sobrescreve_padrao(monkeypatch):
    monkeypatch.setenv("PIPER_DEFAULT_VOICE", "pt_BR-cadu-medium")
    assert modulo_piper.voz_padrao() == "pt_BR-cadu-medium"
    assert BackendPiper().resolver_voz("") == "pt_BR-cadu-medium"
    assert (
        BackendPiper().resolver_voz("pt-BR-ThalitaMultilingualNeural")
        == "pt_BR-cadu-medium"
    )


def test_voz_padrao_sem_env_eh_faber():
    assert modulo_piper.voz_padrao() == "pt_BR-faber-medium"

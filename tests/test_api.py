"""Testes da API (Fase 2: bugs B1-B4 corrigidos)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import main

RAIZ = str(Path(__file__).resolve().parent.parent)

ENV_BASE = {
    "PATH": os.environ.get("PATH", ""),
    "PYTHONDONTWRITEBYTECODE": "1",
    "REQUIRE_API_KEY": "false",
    "API_KEY": "teste",
}


def test_modelos_sem_cabecalho(client):
    r = client.get("/v1/models")
    assert r.status_code == 200
    ids = [m["id"] for m in r.json()["data"]]
    assert "tts-1" in ids
    assert "tts-1-hd" in ids


def test_speech_feliz(client, audio_falso):
    r = client.post(
        "/v1/audio/speech",
        json={"input": "oi", "model": "tts-1"},
        headers={"Authorization": "Bearer qualquer"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
    assert len(r.content) > 0
    assert audio_falso["chamadas"][0] == ("oi", "pt-BR-ThalitaMultilingualNeural", "mp3", 1.0)
    # O app apaga o temporário depois da resposta (BackgroundTasks + os.unlink).
    assert not os.path.exists(audio_falso["caminhos"][0])


def test_auth_chave_certa(client, audio_falso, monkeypatch):
    monkeypatch.setattr(main, "EXIGIR_CHAVE_API", True)
    monkeypatch.setattr(main, "CHAVE_API", "segredo")
    r = client.post("/v1/audio/speech", json={"input": "oi"}, headers={"Authorization": "Bearer segredo"})
    assert r.status_code == 200


def test_auth_chave_errada(client, audio_falso, monkeypatch):
    monkeypatch.setattr(main, "EXIGIR_CHAVE_API", True)
    monkeypatch.setattr(main, "CHAVE_API", "segredo")
    r = client.post("/v1/audio/speech", json={"input": "oi"}, headers={"Authorization": "Bearer errada"})
    assert r.status_code == 401
    assert r.headers.get("www-authenticate") == "Bearer"


def test_auth_esquema_basic_rejeitado(client, audio_falso, monkeypatch):
    monkeypatch.setattr(main, "EXIGIR_CHAVE_API", True)
    monkeypatch.setattr(main, "CHAVE_API", "segredo")
    r = client.post("/v1/audio/speech", json={"input": "oi"}, headers={"Authorization": "Basic abc"})
    assert r.status_code == 401
    assert r.headers.get("www-authenticate") == "Bearer"


def test_auth_sem_cabecalho(client, audio_falso, monkeypatch):
    # Com a checagem ligada, sem cabeçalho é 401 (HTTPBearer auto_error=False
    # devolve None para cabeçalho ausente ou esquema diferente de Bearer).
    monkeypatch.setattr(main, "EXIGIR_CHAVE_API", True)
    monkeypatch.setattr(main, "CHAVE_API", "segredo")
    r = client.post("/v1/audio/speech", json={"input": "oi"})
    assert r.status_code == 401
    assert r.headers.get("www-authenticate") == "Bearer"


def test_auth_sem_chave_configurada(client, audio_falso, monkeypatch):
    # A ausência de CHAVE_API vem primeiro: 500 mesmo sem cabeçalho.
    monkeypatch.setattr(main, "EXIGIR_CHAVE_API", True)
    monkeypatch.setattr(main, "CHAVE_API", None)
    r = client.post("/v1/audio/speech", json={"input": "oi"}, headers={"Authorization": "Bearer segredo"})
    assert r.status_code == 500


def test_auth_sem_chave_configurada_sem_cabecalho(client, audio_falso, monkeypatch):
    monkeypatch.setattr(main, "EXIGIR_CHAVE_API", True)
    monkeypatch.setattr(main, "CHAVE_API", None)
    r = client.post("/v1/audio/speech", json={"input": "oi"})
    assert r.status_code == 500


def test_texto_vazio_devolve_400(client, audio_falso):
    r = client.post("/v1/audio/speech", json={"input": ""}, headers={"Authorization": "Bearer x"})
    assert r.status_code == 400


def test_texto_que_so_esvazia_apos_filtro_mantem_comportamento(client, audio_falso):
    # Caracterização: texto que só fica vazio depois do filtro (ex.: só emoji)
    # mantém o comportamento atual — gera áudio com texto vazio (200).
    r = client.post(
        "/v1/audio/speech",
        json={"input": "🌎🎉🔥"},
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 200
    assert audio_falso["chamadas"][0][0] == ""


def test_formato_desconhecido_cai_em_mpeg(client, audio_falso):
    r = client.post(
        "/v1/audio/speech",
        json={"input": "oi", "response_format": "xyz"},
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"


def test_formato_wav(client, audio_falso):
    r = client.post(
        "/v1/audio/speech",
        json={"input": "oi", "response_format": "wav"},
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/wav"


def test_b1_sem_cabecalho_com_checagem_desligada(client, audio_falso, monkeypatch):
    # B1 corrigido: com REQUIRE_API_KEY=false a rota passa sem Authorization.
    monkeypatch.setattr(main, "EXIGIR_CHAVE_API", False)
    r = client.post("/v1/audio/speech", json={"input": "oi"})
    assert r.status_code == 200


def test_b2_speed_3_devolve_422(client, audio_falso):
    # B2 corrigido: speed acima de 2.0 é rejeitado pelo Pydantic (422).
    r = client.post(
        "/v1/audio/speech",
        json={"input": "oi", "speed": 3.0},
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 422
    detalhe = r.json()["detail"]
    assert any("speed" in str(erro.get("loc")) for erro in detalhe)


def test_b3_velocidade_padrao_respeitada(client, audio_falso, monkeypatch):
    # B3 corrigido: sem speed no corpo, vale VELOCIDADE_PADRAO.
    monkeypatch.setattr(main, "VELOCIDADE_PADRAO", 1.5)
    r = client.post("/v1/audio/speech", json={"input": "oi"}, headers={"Authorization": "Bearer x"})
    assert r.status_code == 200
    assert audio_falso["chamadas"][0][3] == 1.5


def test_b3_formato_padrao_respeitado(client, audio_falso, monkeypatch):
    # B3 corrigido: sem response_format no corpo, vale FORMATO_RESPOSTA_PADRAO.
    monkeypatch.setattr(main, "FORMATO_RESPOSTA_PADRAO", "wav")
    r = client.post("/v1/audio/speech", json={"input": "oi"}, headers={"Authorization": "Bearer x"})
    assert r.status_code == 200
    assert audio_falso["chamadas"][0][2] == "wav"


def test_b4_texto_vazio_devolve_400(client, audio_falso):
    # B4 corrigido: input vazio é 400 (não mais reempacotado como 500).
    r = client.post("/v1/audio/speech", json={"input": ""}, headers={"Authorization": "Bearer x"})
    assert r.status_code == 400


def test_speed_limites_aceitos(client, audio_falso):
    for velocidade in (0.25, 2.0):
        r = client.post(
            "/v1/audio/speech",
            json={"input": "oi", "speed": velocidade},
            headers={"Authorization": "Bearer x"},
        )
        assert r.status_code == 200


def test_speed_fora_dos_limites_devolve_422(client, audio_falso):
    for velocidade in (0.24, 2.01):
        r = client.post(
            "/v1/audio/speech",
            json={"input": "oi", "speed": velocidade},
            headers={"Authorization": "Bearer x"},
        )
        assert r.status_code == 422
        detalhe = r.json()["detail"]
        assert any("speed" in str(erro.get("loc")) for erro in detalhe)


def test_speed_enviado_vence_padrao(client, audio_falso, monkeypatch):
    monkeypatch.setattr(main, "VELOCIDADE_PADRAO", 1.5)
    r = client.post(
        "/v1/audio/speech",
        json={"input": "oi", "speed": 1.0},
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 200
    assert audio_falso["chamadas"][0][3] == 1.0


def test_formato_enviado_vence_padrao(client, audio_falso, monkeypatch):
    monkeypatch.setattr(main, "FORMATO_RESPOSTA_PADRAO", "wav")
    r = client.post(
        "/v1/audio/speech",
        json={"input": "oi", "response_format": "mp3"},
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 200
    assert audio_falso["chamadas"][0][2] == "mp3"


def test_variaveis_mortas_removidas():
    # DEFAULT_LANGUAGE e EXPAND_API não existem mais: conferir lendo
    # somente config.py e .env.example.
    config = (Path(RAIZ) / "config.py").read_text(encoding="utf-8")
    exemplo = (Path(RAIZ) / ".env.example").read_text(encoding="utf-8")
    for morta in ("DEFAULT_LANGUAGE", "EXPAND_API"):
        assert morta not in config
        assert morta not in exemplo


@pytest.mark.parametrize("variavel,valor", [
    ("PORT", "abc"),
    ("PORT", "0"),
    ("PORT", "70000"),
    ("DEFAULT_SPEED", "abc"),
    ("DEFAULT_SPEED", "9"),
    ("DEFAULT_RESPONSE_FORMAT", "xyz"),
])
def test_config_invalida_falha_na_importacao(variavel, valor):
    env = dict(ENV_BASE)
    env[variavel] = valor
    proc = subprocess.run(
        [sys.executable, "-c", f"import sys; sys.path.insert(0, {RAIZ!r}); import main"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode != 0
    saida = proc.stdout + proc.stderr
    assert f"Configuração inválida: {variavel}='{valor}'" in saida

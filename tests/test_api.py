"""Caracterização da API (comportamento atual) + bugs B1-B4 como xfail estrito."""

import os

import pytest

import main


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


def test_auth_sem_cabecalho(client, audio_falso, monkeypatch):
    # 403 nas versões fixadas (HTTPBearer com auto_error); 401 em Starlette novo.
    monkeypatch.setattr(main, "EXIGIR_CHAVE_API", True)
    monkeypatch.setattr(main, "CHAVE_API", "segredo")
    r = client.post("/v1/audio/speech", json={"input": "oi"})
    assert r.status_code in (401, 403)


def test_auth_sem_chave_configurada(client, audio_falso, monkeypatch):
    monkeypatch.setattr(main, "EXIGIR_CHAVE_API", True)
    monkeypatch.setattr(main, "CHAVE_API", None)
    r = client.post("/v1/audio/speech", json={"input": "oi"}, headers={"Authorization": "Bearer segredo"})
    assert r.status_code == 500


def test_texto_vazio_comportamento_real(client, audio_falso):
    # Caracteriza o comportamento atual: o HTTPException(400) é capturado
    # pelo except genérico e reempacotado como 500 (bug B4).
    r = client.post("/v1/audio/speech", json={"input": ""}, headers={"Authorization": "Bearer x"})
    assert r.status_code == 500


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


@pytest.mark.xfail(strict=True, reason="B1: main.py:18 (HTTPBearer auto_error) — ver docs/aplicacao/README.md item 14")
def test_b1_sem_cabecalho_com_checagem_desligada(client, audio_falso, monkeypatch):
    monkeypatch.setattr(main, "EXIGIR_CHAVE_API", False)
    r = client.post("/v1/audio/speech", json={"input": "oi"})
    assert r.status_code == 200


@pytest.mark.xfail(strict=True, reason="B2: tts_handler.py:44-45 (velocidade_para_taxa) + main.py:95-99 — ver docs/aplicacao/README.md item 1")
def test_b2_speed_3_deveria_ser_422(client, audio_falso):
    r = client.post(
        "/v1/audio/speech",
        json={"input": "oi", "speed": 3.0},
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 422


@pytest.mark.xfail(strict=True, reason="B3: main.py:36-37 lidas mas ignoradas em main.py:81-85 — ver docs/aplicacao/README.md item 2")
def test_b3_velocidade_padrao_respeitada(client, audio_falso, monkeypatch):
    monkeypatch.setattr(main, "VELOCIDADE_PADRAO", 1.5)
    r = client.post("/v1/audio/speech", json={"input": "oi"}, headers={"Authorization": "Bearer x"})
    assert r.status_code == 200
    assert audio_falso["chamadas"][0][3] == 1.5


@pytest.mark.xfail(strict=True, reason="B3: main.py:36-37 lidas mas ignoradas em main.py:81-85 — ver docs/aplicacao/README.md item 2")
def test_b3_formato_padrao_respeitado(client, audio_falso, monkeypatch):
    monkeypatch.setattr(main, "FORMATO_RESPOSTA_PADRAO", "wav")
    r = client.post("/v1/audio/speech", json={"input": "oi"}, headers={"Authorization": "Bearer x"})
    assert r.status_code == 200
    assert audio_falso["chamadas"][0][2] == "wav"


@pytest.mark.xfail(strict=True, reason="B4: main.py:74-75 capturado por main.py:95-99 — ver docs/aplicacao/README.md (fluxo, item 2)")
def test_b4_texto_vazio_deveria_ser_400(client, audio_falso):
    r = client.post("/v1/audio/speech", json={"input": ""}, headers={"Authorization": "Bearer x"})
    assert r.status_code == 400

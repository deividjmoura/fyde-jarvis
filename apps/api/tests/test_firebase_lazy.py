"""#5 — o Firebase não pode impedir o boot da API.

Bug real: `credentials.Certificate({})` rodava na importação do módulo e a API
não subia nem com o `{}` recomendado pelo `.env.example`. Agora o init é lazy.
"""

import pytest

import app.services.firebase as fb


def test_importar_com_credencial_vazia_nao_quebra():
    # Se este teste coletar/importar, o import já não lança. Mas explicitamos:
    assert hasattr(fb, "verify_firebase_token")


@pytest.mark.parametrize("branco", ["", "   ", "{}", None])
def test_is_blank(branco):
    assert fb._is_blank(branco) is True


@pytest.mark.parametrize("nao_branco", ['{"project_id": "x"}', ' { "a": 1 } '])
def test_is_blank_negativo(nao_branco):
    assert fb._is_blank(nao_branco) is False


def test_verificar_sem_config_lanca_mensagem_clara(monkeypatch):
    monkeypatch.setattr(fb.settings, "FIREBASE_CREDENTIALS", "{}")
    monkeypatch.setattr(fb, "_inicializado", False)

    with pytest.raises(RuntimeError, match="Firebase não configurado"):
        fb.verify_firebase_token("qualquer-token")


def test_verificar_sem_config_nao_inicializa(monkeypatch):
    """Com credencial vazia, o init nunca marca `_inicializado`."""
    monkeypatch.setattr(fb.settings, "FIREBASE_CREDENTIALS", "{}")
    monkeypatch.setattr(fb, "_inicializado", False)

    with pytest.raises(RuntimeError):
        fb.verify_firebase_token("t")

    assert fb._inicializado is False

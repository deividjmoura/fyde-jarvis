"""Tool de data/hora — em particular o fuso horário.

A API roda em UTC na nuvem; para um assistente brasileiro a hora errada é um
bug visível. Estes testes travam o fuso configurável.
"""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.services.agents.tools.clock import get_current_time

FORMATO_BR = re.compile(r"^\d{2}/\d{2}/\d{4} • \d{2}:\d{2}:\d{2}$")


def test_formato_brasileiro():
    assert FORMATO_BR.match(get_current_time.invoke({}))


def test_respeita_o_fuso_configurado(monkeypatch):
    monkeypatch.setattr(settings, "JARVIS_TIMEZONE", "America/Sao_Paulo")
    esperado = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y • %H")
    assert get_current_time.invoke({}).startswith(esperado)


def test_fuso_diferente_muda_a_hora(monkeypatch):
    monkeypatch.setattr(settings, "JARVIS_TIMEZONE", "Asia/Tokyo")
    toquio = get_current_time.invoke({})

    monkeypatch.setattr(settings, "JARVIS_TIMEZONE", "America/Sao_Paulo")
    brasil = get_current_time.invoke({})

    hora_toquio = int(toquio.split("• ")[1][:2])
    hora_brasil = int(brasil.split("• ")[1][:2])
    # Tóquio está 12h à frente de Brasília; a diferença exata depende do
    # instante da execução, mas nunca pode ser zero nos fusos testados.
    assert hora_toquio != hora_brasil


def test_fuso_invalido_nao_derruba_a_tool(monkeypatch):
    """Container sem tzdata ou fuso errado → cai no relógio local, não explode."""
    monkeypatch.setattr(settings, "JARVIS_TIMEZONE", "Planeta/Marte")
    assert FORMATO_BR.match(get_current_time.invoke({}))

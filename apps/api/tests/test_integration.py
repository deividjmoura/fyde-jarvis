"""Testes de integração: chamadas HTTP REAIS contra a Open-Meteo.

Ficam fora da suíte padrão (veja `addopts` no pytest.ini) para o CI não depender
de rede externa. Rode com:

    pytest -m integration -v
"""

import pytest

from app.services.agents.tools import weather


@pytest.mark.integration
async def test_open_meteo_responde_de_verdade_para_itajai():
    saida = await weather.get_weather.ainvoke({"city": "Itajaí"})

    assert "Itajaí" in saida
    assert "Clima agora em" in saida
    # A temperatura precisa ser um número, não a mensagem de erro.
    assert "Não encontrei" not in saida
    assert "Não consegui consultar" not in saida


@pytest.mark.integration
async def test_open_meteo_rejeita_cidade_inexistente():
    saida = await weather.get_weather.ainvoke({"city": "Zzzqqxxnãoexiste"})

    assert "Não encontrei a cidade" in saida

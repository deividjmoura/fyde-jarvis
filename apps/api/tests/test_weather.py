"""Tool de clima (Open-Meteo) com HTTP mockado via respx.

Chamadas reais ficam em test_integration.py, marcadas como `integration`.
"""

import httpx
import pytest
import respx

from app.services.agents.tools import weather

PLACE = {
    "name": "Itajaí",
    "latitude": -26.90778,
    "longitude": -48.66194,
    "admin1": "Santa Catarina",
    "country": "Brasil",
}

FORECAST_OK = {
    "current_units": {"temperature_2m": "°C", "wind_speed_10m": "km/h"},
    "current": {
        "temperature_2m": 21.5,
        "relative_humidity_2m": 64,
        "apparent_temperature": 23.2,
        "weather_code": 2,
        "wind_speed_10m": 6.6,
    },
    "daily": {
        "temperature_2m_max": [21.5],
        "temperature_2m_min": [13.6],
        "precipitation_probability_max": [88],
        "weather_code": [51],
    },
}


@pytest.mark.parametrize(
    "codigo,esperado",
    [
        (0, "céu limpo"),
        (2, "parcialmente nublado"),
        (51, "garoa leve"),
        (95, "trovoada"),
    ],
)
def test_traducao_dos_codigos_wmo(codigo, esperado):
    assert weather.describe_weather_code(codigo) == esperado


def test_codigo_desconhecido_nao_estoura():
    assert "código WMO 999" in weather.describe_weather_code(999)


def test_codigo_none():
    assert weather.describe_weather_code(None) == "condição não informada"


@respx.mock
async def test_get_weather_sucesso():
    respx.get(weather.GEOCODING_URL).mock(
        return_value=httpx.Response(200, json={"results": [PLACE]})
    )
    respx.get(weather.FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_OK)
    )

    saida = await weather.get_weather.ainvoke({"city": "Itajaí"})

    assert "Itajaí, Santa Catarina, Brasil" in saida
    assert "21.5°C" in saida
    assert "parcialmente nublado" in saida
    assert "mín 13.6°C" in saida
    assert "máx 21.5°C" in saida
    assert "88% de chance de chuva" in saida


@respx.mock
async def test_cidade_nao_encontrada():
    respx.get(weather.GEOCODING_URL).mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    saida = await weather.get_weather.ainvoke({"city": "Xyzabc"})

    assert "Não encontrei a cidade" in saida
    assert "Xyzabc" in saida


@respx.mock
async def test_cidade_vazia_nao_chama_rede():
    rota = respx.get(weather.GEOCODING_URL).mock(
        return_value=httpx.Response(200, json={"results": [PLACE]})
    )

    saida = await weather.get_weather.ainvoke({"city": "   "})

    assert "Preciso do nome de uma cidade" in saida
    assert rota.call_count == 0


@respx.mock
async def test_erro_http_vira_mensagem_amigavel():
    respx.get(weather.GEOCODING_URL).mock(return_value=httpx.Response(503))

    saida = await weather.get_weather.ainvoke({"city": "Itajaí"})

    assert "respondeu com erro" in saida


@respx.mock
async def test_timeout_vira_mensagem_amigavel():
    respx.get(weather.GEOCODING_URL).mock(side_effect=httpx.ReadTimeout("boom"))

    saida = await weather.get_weather.ainvoke({"city": "Itajaí"})

    assert "demorou demais" in saida


@respx.mock
async def test_previsao_sem_diario_nao_quebra():
    """Se a API não devolver o bloco `daily`, a resposta atual ainda sai."""
    respx.get(weather.GEOCODING_URL).mock(
        return_value=httpx.Response(200, json={"results": [PLACE]})
    )
    respx.get(weather.FORECAST_URL).mock(
        return_value=httpx.Response(200, json={"current": FORECAST_OK["current"]})
    )

    saida = await weather.get_weather.ainvoke({"city": "Itajaí"})

    assert "Clima agora em Itajaí" in saida
    assert "mín" not in saida

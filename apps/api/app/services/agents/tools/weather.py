"""Clima via Open-Meteo — **sem API key**.

Fluxo em duas chamadas:
1. geocodificação: nome da cidade → latitude/longitude
2. previsão: par de coordenadas → condição atual + mín/máx do dia

Tudo `async` com `httpx.AsyncClient`: uma tool síncrona de HTTP bloquearia o
event loop do agente ReAct inteiro durante a chamada de rede.

As tools **nunca levantam exceção** — devolvem uma string em pt-BR, para que o
agente consiga explicar o problema ao usuário em vez de quebrar o turno.
"""

import logging

import httpx
from langchain_core.tools import tool

from app.core.config import settings

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

_CURRENT_FIELDS = (
    "temperature_2m,relative_humidity_2m,apparent_temperature,"
    "weather_code,wind_speed_10m"
)
_DAILY_FIELDS = (
    "temperature_2m_max,temperature_2m_min,"
    "precipitation_probability_max,weather_code"
)

# Códigos WMO de condição do tempo → descrição em pt-BR.
# Fonte: https://open-meteo.com/en/docs ("WMO Weather interpretation codes")
WMO_CODES: dict[int, str] = {
    0: "céu limpo",
    1: "predominantemente limpo",
    2: "parcialmente nublado",
    3: "nublado",
    45: "névoa",
    48: "névoa com deposição de geada",
    51: "garoa leve",
    53: "garoa moderada",
    55: "garoa intensa",
    56: "garoa congelante leve",
    57: "garoa congelante intensa",
    61: "chuva fraca",
    63: "chuva moderada",
    65: "chuva forte",
    66: "chuva congelante leve",
    67: "chuva congelante forte",
    71: "neve fraca",
    73: "neve moderada",
    75: "neve forte",
    77: "grãos de neve",
    80: "pancadas de chuva fracas",
    81: "pancadas de chuva moderadas",
    82: "pancadas de chuva violentas",
    85: "pancadas de neve fracas",
    86: "pancadas de neve fortes",
    95: "trovoada",
    96: "trovoada com granizo leve",
    99: "trovoada com granizo forte",
}


def describe_weather_code(code) -> str:
    """Traduz um código WMO para português; nunca falha."""
    if code is None:
        return "condição não informada"
    return WMO_CODES.get(int(code), f"condição desconhecida (código WMO {code})")


def _place_label(place: dict) -> str:
    """'Itajaí, Santa Catarina, Brasil' — só as partes que existem."""
    parts = [place.get("name"), place.get("admin1"), place.get("country")]
    return ", ".join(p for p in parts if p)


async def _geocode(client: httpx.AsyncClient, city: str) -> dict | None:
    response = await client.get(
        GEOCODING_URL,
        params={"name": city, "count": 1, "language": "pt", "format": "json"},
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    return results[0] if results else None


async def _forecast(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    response = await client.get(
        FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": _CURRENT_FIELDS,
            "daily": _DAILY_FIELDS,
            "timezone": "auto",
            "forecast_days": 1,
        },
    )
    response.raise_for_status()
    return response.json()


def _format(place: dict, data: dict) -> str:
    current = data.get("current") or {}
    units = data.get("current_units") or {}
    daily = data.get("daily") or {}

    temp_unit = units.get("temperature_2m", "°C")
    wind_unit = units.get("wind_speed_10m", "km/h")

    lines = [
        f"Clima agora em {_place_label(place)}: "
        f"{current.get('temperature_2m')}{temp_unit}, "
        f"{describe_weather_code(current.get('weather_code'))}.",
        f"Sensação térmica de {current.get('apparent_temperature')}{temp_unit}, "
        f"umidade {current.get('relative_humidity_2m')}% "
        f"e vento de {current.get('wind_speed_10m')}{wind_unit}.",
    ]

    t_max = (daily.get("temperature_2m_max") or [None])[0]
    t_min = (daily.get("temperature_2m_min") or [None])[0]
    precip = (daily.get("precipitation_probability_max") or [None])[0]
    daily_code = (daily.get("weather_code") or [None])[0]

    if t_min is not None and t_max is not None:
        resumo = (
            f"Para hoje: mín {t_min}{temp_unit}, máx {t_max}{temp_unit}, "
            f"{describe_weather_code(daily_code)}"
        )
        if precip is not None:
            resumo += f" e {precip}% de chance de chuva"
        lines.append(resumo + ".")

    return " ".join(lines)


@tool
async def get_weather(city: str) -> str:
    """Consulta o clima atual e a previsão de hoje para uma cidade. Use o nome da cidade, por exemplo 'Itajaí' ou 'São Paulo'."""
    cidade = (city or "").strip()
    if not cidade:
        return "Preciso do nome de uma cidade para consultar o clima."

    try:
        async with httpx.AsyncClient(
            timeout=settings.WEATHER_TIMEOUT_SECONDS,
            headers={"User-Agent": settings.HTTP_USER_AGENT},
        ) as client:
            place = await _geocode(client, cidade)
            if place is None:
                return (
                    f"Não encontrei a cidade \"{cidade}\". "
                    "Confere o nome ou tenta com o estado junto, tipo \"Florianópolis, SC\"."
                )
            data = await _forecast(
                client, place["latitude"], place["longitude"]
            )
            return _format(place, data)
    except httpx.TimeoutException:
        logger.warning("Timeout consultando clima de %r", cidade)
        return "O serviço de clima demorou demais para responder. Tenta de novo em instantes."
    except httpx.HTTPStatusError as exc:
        logger.warning("HTTP %s ao consultar clima de %r", exc.response.status_code, cidade)
        return "O serviço de clima respondeu com erro agora. Tenta de novo em instantes."
    except Exception:
        logger.exception("Falha inesperada ao consultar clima de %r", cidade)
        return "Não consegui consultar o clima agora."

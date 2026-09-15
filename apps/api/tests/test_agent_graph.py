"""Teste de ponta a ponta do grafo ReAct com um LLM falso.

Prova o elo mais frágil da mudança: uma tool `async` realmente executa dentro do
LangGraph (o ToolNode a invoca por `ainvoke`), sem depender de OpenRouter.
O HTTP é mockado para o teste ser determinístico.

NOTA: `create_react_agent` de `langgraph.prebuilt` está deprecated no LangGraph
1.0 (avisa para migrar a `langchain.agents.create_agent`). A migração é
deliberadamente feita fora desta branch — veja o AGENT_SYNC.md.
"""

import warnings

import httpx
import respx
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent

from app.services.agents.first_agent import SYSTEM_PROMPT, tools
from app.services.agents.tools import weather


class FakeToolCallingModel(GenericFakeChatModel):
    """Fake que aceita `bind_tools` — o grafo exige isso do modelo."""

    def bind_tools(self, tools, **kwargs):  # noqa: D102
        return self


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
        "temperature_2m": 21.4,
        "relative_humidity_2m": 65,
        "apparent_temperature": 22.8,
        "weather_code": 2,
        "wind_speed_10m": 7.7,
    },
    "daily": {
        "temperature_2m_max": [21.5],
        "temperature_2m_min": [13.6],
        "precipitation_probability_max": [88],
        "weather_code": [51],
    },
}


@respx.mock
async def test_grafo_executa_tool_async_e_chega_na_resposta_final():
    respx.get(weather.GEOCODING_URL).mock(
        return_value=httpx.Response(200, json={"results": [PLACE]})
    )
    respx.get(weather.FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_OK)
    )

    turnos = iter(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_weather",
                        "args": {"city": "Itajaí"},
                        "id": "call_1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Está 21 graus em Itajaí, com garoa leve."),
        ]
    )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        agent = create_react_agent(
            model=FakeToolCallingModel(messages=turnos),
            tools=tools,
            prompt=SYSTEM_PROMPT,
        )
        resultado = await agent.ainvoke(
            {"messages": [("user", "como está o clima em Itajaí?")]}
        )

    tipos = [m.type for m in resultado["messages"]]
    assert tipos == ["human", "ai", "tool", "ai"]

    mensagem_tool = resultado["messages"][2]
    assert "Itajaí, Santa Catarina, Brasil" in mensagem_tool.content
    assert "21.4°C" in mensagem_tool.content

    assert resultado["messages"][-1].content == "Está 21 graus em Itajaí, com garoa leve."

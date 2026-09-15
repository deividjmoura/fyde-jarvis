"""Tools do agente Fyde Jarvis.

Cada tool vive num módulo próprio. `ALL_TOOLS` é a lista canônica que
`first_agent.py` reexporta como `tools`.

⚠️  CONTRATO PÚBLICO: outros módulos do repo importam `tools` e
`SYSTEM_PROMPT` de `app.services.agents.first_agent`. Se você mudar o nome
desta lista ou reorganizar as exports, avise no AGENT_SYNC.md antes.
"""

from app.services.agents.tools.calculator import simple_calculator
from app.services.agents.tools.clock import get_current_time
from app.services.agents.tools.weather import get_weather
from app.services.agents.tools.search import web_search

ALL_TOOLS = [
    get_current_time,
    simple_calculator,
    get_weather,
    web_search,
]

__all__ = [
    "ALL_TOOLS",
    "get_current_time",
    "simple_calculator",
    "get_weather",
    "web_search",
]

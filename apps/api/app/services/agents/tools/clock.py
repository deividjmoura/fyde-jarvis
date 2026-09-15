"""Data e hora.

A API roda na nuvem (Render), onde o relógio do servidor é UTC — para um
assistente brasileiro isso devolve hora errada. Por isso o fuso é explícito
via `JARVIS_TIMEZONE` (padrão `America/Sao_Paulo`), e não `datetime.now()`.
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain_core.tools import tool

from app.core.config import settings

logger = logging.getLogger(__name__)


def _now():
    """`datetime` no fuso configurado, com fallback para o relógio local."""
    try:
        return datetime.now(ZoneInfo(settings.JARVIS_TIMEZONE))
    except (ZoneInfoNotFoundError, ValueError) as exc:
        # Fuso inválido ou base de dados de fusos ausente no container.
        # Cai no comportamento antigo em vez de derrubar a tool.
        logger.warning(
            "Fuso %r indisponível (%s); usando relógio local do servidor.",
            settings.JARVIS_TIMEZONE,
            exc,
        )
        return datetime.now()


@tool
def get_current_time() -> str:
    """Retorna a data e hora atual no formato brasileiro."""
    return _now().strftime("%d/%m/%Y • %H:%M:%S")

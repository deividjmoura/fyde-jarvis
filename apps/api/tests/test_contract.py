"""Guarda do contrato público entre os dois times.

O AGENT_SYNC.md registra que outro módulo do repo faz:

    from app.services.agents.first_agent import SYSTEM_PROMPT, tools

Estes testes existem para que uma reorganização interna de `first_agent.py`
quebre a suíte AQUI, em vez de quebrar o código do outro time em produção.
"""

from langchain_core.messages import SystemMessage


def test_first_agent_exporta_o_contrato_publico():
    from app.services.agents import first_agent

    for nome in ("SYSTEM_PROMPT", "tools", "run_first_agent"):
        assert hasattr(first_agent, nome), (
            f"first_agent.{nome} sumiu — outros módulos importam este nome. "
            "Se a mudança foi de propósito, avise no AGENT_SYNC.md."
        )

    assert isinstance(first_agent.SYSTEM_PROMPT, SystemMessage)
    assert isinstance(first_agent.tools, list)
    assert first_agent.tools, "tools não pode ser uma lista vazia"


def test_import_direto_dos_nomes_funciona():
    # Literalmente o import que o outro time usa.
    from app.services.agents.first_agent import (  # noqa: F401
        SYSTEM_PROMPT,
        run_first_agent,
        tools,
    )


def test_modulo_de_streaming_do_outro_time_ainda_carrega():
    """`services/agents/streaming.py` faz `from ...first_agent import SYSTEM_PROMPT, tools`.

    Este teste só importa o módulo (sem depender dos nomes de função dele), para
    que uma reorganização minha quebre a suíte AQUI em vez de quebrar o SSE em
    produção. `importorskip` porque o arquivo pertence à outra branch.
    """
    import pytest

    pytest.importorskip("app.services.agents.streaming")


def test_todas_as_tools_tem_nome_e_descricao():
    """O LangGraph usa `name` e a docstring para decidir quando chamar a tool."""
    from app.services.agents.first_agent import tools

    for t in tools:
        assert t.name, "toda tool precisa de nome"
        assert t.description and t.description.strip(), (
            f"tool {t.name!r} sem docstring — o modelo não vai saber quando usá-la"
        )


def test_tools_incluem_as_quatro_esperadas():
    from app.services.agents.first_agent import tools

    nomes = {t.name for t in tools}
    assert {"get_current_time", "simple_calculator", "get_weather", "web_search"} <= nomes


def test_tools_nao_tem_nome_duplicado():
    from app.services.agents.first_agent import tools

    nomes = [t.name for t in tools]
    assert len(nomes) == len(set(nomes)), f"tools duplicadas: {nomes}"

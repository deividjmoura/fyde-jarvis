"""Streaming de respostas do agente (SSE).

Criado na tarefa de Streaming. Importamos apenas `SYSTEM_PROMPT` e `tools`
de first_agent (leitura) — se o módulo de tools for reorganizado por outro
time, ajustar o import aqui (ver AGENT_SYNC.md).
"""

import json
from typing import AsyncGenerator, Any

from langchain_core.messages import HumanMessage, AIMessageChunk
from langgraph.prebuilt import create_react_agent

from app.core.checkpointer import get_checkpointer
from app.services.llm.provider import get_llm
from app.services.agents.first_agent import SYSTEM_PROMPT, tools


def _text_from_content(content: Any) -> str:
    """Normaliza o conteúdo do chunk (str ou lista de blocos) para texto."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


async def astream_agent_tokens(
    query: str, thread_id: str
) -> AsyncGenerator[str, None]:
    """Emite pedaços (tokens/chunks) da resposta final do agente.

    Usa stream_mode="messages": cada item é (message_chunk, metadata).
    Filtramos o nó "agent" (fala do LLM) e ignoramos chamadas/retornos
    de tools, para o cliente receber só o texto da resposta.
    """
    checkpointer = await get_checkpointer()
    agent = create_react_agent(
        model=get_llm(),
        tools=tools,
        checkpointer=checkpointer,
        prompt=SYSTEM_PROMPT,
    )

    inputs = {"messages": [HumanMessage(content=query)]}
    config = {"configurable": {"thread_id": thread_id}}

    async for chunk, metadata in agent.astream(
        inputs, config=config, stream_mode="messages"
    ):
        if metadata.get("langgraph_node") != "agent":
            continue
        if isinstance(chunk, AIMessageChunk):
            text = _text_from_content(chunk.content)
            if text:
                yield text


def sse_pack(payload: dict) -> str:
    """Serializa um evento SSE (`data: {json}\\n\\n`)."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

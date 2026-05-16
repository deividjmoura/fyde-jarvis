from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from datetime import datetime
import os
from app.core.checkpointer import get_checkpointer

@tool
def get_current_time() -> str:
    """Retorna a data e hora atual."""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

@tool
def simple_calculator(expression: str) -> str:
    """Faz cálculos matemáticos."""
    try:
        result = eval(expression)
        return f"O resultado é {result}"
    except:
        return "Não consegui calcular esta expressão."

tools = [get_current_time, simple_calculator]

def get_llm():
    return ChatOpenAI(
        model="anthropic/claude-3-haiku",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0.7,
    )

async def run_first_agent(query: str, thread_id: str):
    checkpointer = await get_checkpointer()
    
    llm = get_llm()
    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer
    )

    inputs = {"messages": [HumanMessage(content=query)]}
    config = {"configurable": {"thread_id": thread_id}}

    response_text = ""
    async for chunk in agent.astream(inputs, config=config):
        if "agent" in chunk:
            for msg in chunk["agent"].get("messages", []):
                if msg.content:
                    response_text = msg.content

    return response_text or "Não consegui processar sua solicitação."
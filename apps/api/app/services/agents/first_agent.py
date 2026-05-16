import os
from dotenv import load_dotenv
from datetime import datetime

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from app.core.checkpointer import get_checkpointer
from app.services.llm.provider import get_llm

# Carrega .env
load_dotenv()
load_dotenv(dotenv_path="../../.env")
load_dotenv(override=True)

print("🔑 OPENROUTER_API_KEY carregada:", "✅ SIM" if os.getenv("OPENROUTER_API_KEY") else "❌ NÃO")

# ====================== SYSTEM PROMPT ======================
SYSTEM_PROMPT = SystemMessage(content="""Você é o **Fyde Jarvis**, um assistente IA brasileiro útil, inteligente e amigável.

- Responda sempre em português brasileiro, de forma natural e direta.
- Use humor leve quando fizer sentido.
- Mantenha a memória da conversa.""")

# ====================== TOOLS ======================
@tool
def get_current_time() -> str:
    """Retorna a data e hora atual no formato brasileiro."""
    return datetime.now().strftime("%d/%m/%Y • %H:%M:%S")

@tool
def simple_calculator(expression: str) -> str:
    """Faz cálculos matemáticos simples."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"O resultado é {result}"
    except:
        return "Não consegui calcular essa expressão."

tools = [get_current_time, simple_calculator]


# ====================== RUN AGENT ======================
async def run_first_agent(query: str, thread_id: str):
    checkpointer = await get_checkpointer()
    llm = get_llm()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer,
        prompt=SYSTEM_PROMPT          # ← Aqui é o correto agora
    )

    inputs = {"messages": [HumanMessage(content=query)]}
    config = {"configurable": {"thread_id": thread_id}}

    response_text = ""
    async for chunk in agent.astream(inputs, config=config):
        if "agent" in chunk:
            for msg in chunk["agent"].get("messages", []):
                if msg.content:
                    response_text = msg.content

    return response_text or "Não consegui responder no momento."
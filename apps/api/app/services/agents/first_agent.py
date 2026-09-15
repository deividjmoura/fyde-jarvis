"""Agente ReAct do Fyde Jarvis.

⚠️  CONTRATO PÚBLICO DESTE MÓDULO (importado por outros módulos do repo):
    - `SYSTEM_PROMPT`
    - `tools`
    - `run_first_agent`
As tools em si moram em `app/services/agents/tools/`; aqui elas são apenas
reexportadas. Se você precisar renomear qualquer coisa acima, avise antes no
AGENT_SYNC.md — há código do outro time fazendo
`from app.services.agents.first_agent import SYSTEM_PROMPT, tools`.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from app.core.checkpointer import get_checkpointer
from app.services.agents.tools import ALL_TOOLS
from app.services.llm.provider import get_llm

# ====================== SYSTEM PROMPT ======================
SYSTEM_PROMPT = SystemMessage(content="""Você é o **Fyde Jarvis**, um assistente IA brasileiro útil, inteligente e amigável.

- Responda sempre em português brasileiro, de forma natural e direta.
- Use humor leve quando fizer sentido.
- Mantenha a memória da conversa.

Você tem tools à disposição — use-as em vez de inventar:
- `get_current_time` para data e hora;
- `simple_calculator` para contas;
- `get_weather` para clima e previsão de uma cidade;
- `web_search` para fatos, pessoas, lugares e coisas que podem ter mudado.

Se uma tool falhar, diga o que aconteceu com naturalidade em vez de fingir que sabe.""")

# ====================== TOOLS ======================
# Reexportadas do pacote `tools/`. Mantenha o nome `tools`: é contrato público.
tools = ALL_TOOLS


# ====================== RUN AGENT ======================
async def run_first_agent(query: str, thread_id: str):
    checkpointer = await get_checkpointer()
    llm = get_llm()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer,
        prompt=SYSTEM_PROMPT
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

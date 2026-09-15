import ast
import operator
from datetime import datetime

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from app.core.checkpointer import get_checkpointer
from app.services.llm.provider import get_llm

# ====================== SYSTEM PROMPT ======================
SYSTEM_PROMPT = SystemMessage(content="""Você é o **Fyde Jarvis**, um assistente IA brasileiro útil, inteligente e amigável.

- Responda sempre em português brasileiro, de forma natural e direta.
- Use humor leve quando fizer sentido.
- Mantenha a memória da conversa.""")

# ====================== CALCULADORA SEGURA (sem eval) ======================
# Avalia a expressão com AST: apenas literais numéricos e operadores
# matemáticos básicos são permitidos — nada de código arbitrário.
_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](
            _eval_node(node.left), _eval_node(node.right)
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Expressão não suportada")


# ====================== TOOLS ======================
@tool
def get_current_time() -> str:
    """Retorna a data e hora atual no formato brasileiro."""
    return datetime.now().strftime("%d/%m/%Y • %H:%M:%S")


@tool
def simple_calculator(expression: str) -> str:
    """Faz cálculos matemáticos simples (+, -, *, /, //, %, ** e parênteses)."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree)
        return f"O resultado é {result}"
    except ZeroDivisionError:
        return "Divisão por zero não rolou — nem com tecnologia Stark."
    except Exception:
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

"""Calculadora segura — sem `eval()`.

Decisão de arquitetura registrada no AGENT_SYNC.md: `eval()` é banido.
A expressão é parseada em AST e apenas literais numéricos e operadores
matemáticos whitelisted são avaliados; qualquer outra coisa (chamada de
função, atributo, nome, import) levanta `ValueError` e vira mensagem amigável.

Comportamento idêntico ao que existia inline em `first_agent.py` — foi apenas
movido para cá.
"""

import ast
import operator

from langchain_core.tools import tool

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

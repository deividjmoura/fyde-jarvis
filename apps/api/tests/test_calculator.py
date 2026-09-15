"""Calculadora segura (AST, sem eval) — incluindo os casos de injeção.

A decisão "eval() banido" está no AGENT_SYNC.md; estes testes são o que impede
alguém de reintroduzir `eval()` sem que a suíte reclame.
"""

import pytest

from app.services.agents.tools.calculator import simple_calculator


def _calc(expression: str) -> str:
    return simple_calculator.invoke({"expression": expression})


@pytest.mark.parametrize(
    "expressao,esperado",
    [
        ("2+3", "O resultado é 5"),
        ("2+3*4", "O resultado é 14"),          # precedência
        ("(2+3)*4", "O resultado é 20"),        # parênteses
        ("10/4", "O resultado é 2.5"),
        ("10//4", "O resultado é 2"),
        ("10%3", "O resultado é 1"),
        ("2**10", "O resultado é 1024"),
        ("-5+3", "O resultado é -2"),
        ("+5", "O resultado é 5"),
        ("2.5*4", "O resultado é 10.0"),
    ],
)
def test_aritmetica(expressao, esperado):
    assert _calc(expressao) == esperado


def test_divisao_por_zero_nao_estoura():
    assert "Divisão por zero" in _calc("(2+3)/0")


@pytest.mark.parametrize(
    "maliciosa",
    [
        "__import__('os').system('echo pwned')",
        "open('/etc/passwd').read()",
        "(1).__class__.__bases__",
        "eval('1+1')",
        "exec('print(1)')",
        "lambda: 1",
        "[x for x in (1,2)]",
        "'a'*3",          # string não é literal numérico permitido
    ],
)
def test_rejeita_codigo(maliciosa):
    """Nada além de números e operadores aritméticos passa."""
    assert _calc(maliciosa) == "Não consegui calcular essa expressão."


def test_expressao_invalida_nao_estoura():
    assert _calc("2 +") == "Não consegui calcular essa expressão."
    assert _calc("") == "Não consegui calcular essa expressão."


def test_nao_existe_eval_no_modulo():
    """Trava explícita da decisão de arquitetura."""
    import inspect

    import app.services.agents.tools.calculator as modulo

    fonte = inspect.getsource(modulo)
    assert "\neval(" not in fonte and "= eval(" not in fonte

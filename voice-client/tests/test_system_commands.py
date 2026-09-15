"""Testes do parser de comandos locais e da confirmação verbal.

Roda sem tocar no PC de verdade: parse_command apenas monta descrições e
callables; a única execução real testada aqui é webbrowser via monkeypatch.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from system_commands import (  # noqa: E402
    parse_command,
    is_confirmation,
    _cmd_open_url,
)


# ------------------------- helpers de ambiente fake ------------------------
def _fake_which(binarios_presentes):
    def fake(binary):
        return f"/usr/bin/{binary}" if binary in binarios_presentes else None
    return fake


@pytest.fixture
def com_desktop(monkeypatch):
    """Simula um desktop com pactl + gnome-screenshot + apps disponíveis."""
    import system_commands
    monkeypatch.setattr(system_commands.shutil, "which", _fake_which(
        {"pactl", "gnome-screenshot", "google-chrome", "code", "firefox",
         "spotify", "kgx"}
    ))


# ------------------------------ parse: volume ------------------------------
@pytest.mark.parametrize("frase,esperado", [
    ("aumenta o volume", "aumentar o volume"),
    ("pode aumentar o volume por favor", "aumentar o volume"),
    ("diminui o volume", "diminuir o volume"),
    ("abaixa o volume", "diminuir o volume"),
    ("muta o som", "mudo"),
    ("desmuta", "mudo"),
])
def test_volume(com_desktop, frase, esperado):
    parsed = parse_command(frase)
    assert parsed is not None, frase
    desc, _action = parsed
    assert esperado in desc


def test_volume_sem_ferramenta_degrada(monkeypatch):
    """Sem pactl/amixer: reconhece a intenção e avisa, não quebra."""
    import system_commands
    monkeypatch.setattr(system_commands.shutil, "which", _fake_which(set()))
    desc, action = parse_command("aumenta o volume")
    assert "sem pactl/amixer" in desc
    assert "pactl" in action()  # executável responde amigavelmente


# ------------------------------ parse: screenshot --------------------------
@pytest.mark.parametrize("frase", [
    "tira um print",
    "tira uma screenshot",
    "captura de tela",
    "print da tela",
])
def test_screenshot(com_desktop, frase):
    parsed = parse_command(frase)
    assert parsed is not None, frase
    assert "print" in parsed[0]


# ------------------------------ parse: URLs --------------------------------
@pytest.mark.parametrize("frase,url", [
    ("abre o google.com", "google.com"),
    ("abrir site https://github.com/deividjmoura", "https://github.com/deividjmoura"),
    ("abra o site globo.com", "globo.com"),
])
def test_abrir_url(frase, url):
    desc, action = parse_command(frase)
    assert url in desc


def test_url_ganha_https(monkeypatch):
    abertas = []
    monkeypatch.setattr("webbrowser.open", lambda u: abertas.append(u))
    _, action = _cmd_open_url("example.com")
    action()
    assert abertas == ["https://example.com"]


# ------------------------------ parse: apps --------------------------------
@pytest.mark.parametrize("frase,app", [
    ("abre o chrome", "chrome"),
    ("abrir o vscode", "vscode"),
    ("abre o spotify", "spotify"),
])
def test_abrir_app(com_desktop, frase, app):
    desc, _ = parse_command(frase)
    assert app in desc


# ------------------------------ parse: negativos (viram cérebro) -----------
@pytest.mark.parametrize("frase", [
    "me conta uma piada",
    "abre aspas vai",          # sem alvo reconhecido
    "o que você acha do chrome",
    "toca uma música",
    "que horas são",
    "abrir a gaveta",
    "",
])
def test_frases_nao_comando(frase):
    assert parse_command(frase) is None, frase


# ------------------------------ confirmação verbal -------------------------
@pytest.mark.parametrize("resp", ["sim", "Sim, pode", "bora", "manda bala",
                                  "confirma", "ok", "beleza", "pode abrir sim"])
def test_confirmacao_afirmativa(resp):
    assert is_confirmation(resp) is True


@pytest.mark.parametrize("resp", ["não", "não quero", "cancela", "deixa quieto",
                                  "negativo", "para", "", "hmm talvez",
                                  "não sei, melhor não"])
def test_confirmacao_negativa_ou_ambigua(resp):
    # padrão seguro: ambiguidade NÃO executa
    assert is_confirmation(resp) is False

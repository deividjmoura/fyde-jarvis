"""
Comandos locais do PC com confirmação verbal (item "Próximo" do roadmap).

Reconhece intenções ESPECÍFICAS por regras (regex) — nunca executa texto
livre vindo do LLM. Fluxo: frase → ação agendada → "Posso executar?" →
só roda com confirmação verbal afirmativa. Padrão seguro: dúvida = cancela.

Cada ação é um par (descrição_humana, callable). A montagem dos comandos de
sistema fica separada da execução para ser testável sem tocar no PC.
"""

import re
import shutil
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Apps conhecidos: nome falado → executáveis nativos (ordem) + ID Flatpak.
# Cobre X11 e Wayland; Arch, Debian, Fedora, openSUSE… Edite à vontade.
# ---------------------------------------------------------------------------
KNOWN_APPS = {
    "chrome": {
        "bins": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"],
        "flatpak": "com.google.Chrome",
    },
    "firefox": {
        "bins": ["firefox"],
        "flatpak": "org.mozilla.firefox",
    },
    "vscode": {
        "bins": ["code", "codium"],
        "flatpak": "com.visualstudio.code",
    },
    "spotify": {
        "bins": ["spotify"],
        "flatpak": "com.spotify.Client",
    },
    "terminal": {
        "bins": ["kgx", "gnome-console", "gnome-terminal", "konsole",
                 "alacritty", "kitty", "foot", "wezterm", "ghostty", "tilix", "xterm"],
        "flatpak": None,
    },
}

AFFIRMATIVE = ("sim", "confirma", "pode", "isso", "bora", "manda", "claro",
               "ok", "beleza", "afirmativo", "executa", "vai", "abre")
NEGATIVE = ("não", "nao", "cancela", "deixa", "para", "negativo", "nope")


def is_confirmation(text: str) -> bool:
    """Confirmação explícita; na dúvida, NÃO executa (padrão seguro)."""
    if not text:
        return False
    t = text.lower().strip()
    if any(n in t for n in NEGATIVE):
        return False
    return any(a in t for a in AFFIRMATIVE)


def _which(candidates):
    for c in candidates:
        path = shutil.which(c)
        if path:
            return path
    return None


def _flatpak_has(app_id: str) -> bool:
    """True se o app flatpak está instalado (checagem rápida e silenciosa)."""
    try:
        r = subprocess.run(["flatpak", "info", app_id],
                           capture_output=True, timeout=4)
        return r.returncode == 0
    except Exception:
        return False


def _resolve_app_argv(app_key: str):
    """Devolve o argv pronto para lançar o app, ou None se não achou.

    Prioridade: binário nativo → Flatpak (se o `flatpak` existir e o ID
    estiver instalado).
    """
    entry = KNOWN_APPS[app_key]
    native = _which(entry["bins"])
    if native:
        return [native]

    flatpak_id = entry.get("flatpak")
    if flatpak_id and shutil.which("flatpak") and _flatpak_has(flatpak_id):
        return ["flatpak", "run", flatpak_id]

    return None


# ---------------------------------------------------------------------------
# Montadores de comando (puros — não executam nada)
# ---------------------------------------------------------------------------
def _cmd_open_url(url: str):
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    desc = f"Vou abrir o site {url} no navegador"
    return desc, lambda: (webbrowser.open(url),
                          f"Aberto: {url}")[1]


def _cmd_open_app(app_key: str):
    argv = _resolve_app_argv(app_key)
    if not argv:
        desc = f"Queria abrir o {app_key}, mas não encontrei ele instalado"
        return desc, lambda: f"{app_key} não está instalado (nativo nem flatpak)."

    def run():
        subprocess.Popen(argv, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        return f"{app_key} aberto."

    return f"Vou abrir o {app_key}", run


def _cmd_volume(direction: str):
    """direction: 'up' | 'down' | 'mute'"""
    if shutil.which("pactl"):
        args = {"up": ["+10%"], "down": ["-10%"], "mute": ["toggle"]}[direction]
        base = (["pactl", "set-sink-volume", "@DEFAULT_SINK@"] if direction != "mute"
                else ["pactl", "set-sink-mute", "@DEFAULT_SINK@"])
        cmd = base + args
    elif shutil.which("amixer"):
        cmd = ["amixer", "-q", "sset", "Master",
               {"up": "10%+", "down": "10%-", "mute": "toggle"}[direction]]
    else:
        return ("Queria mexer no volume, mas sem pactl/amixer disponível",
                lambda: "Sem pactl nem amixer por aqui.")

    labels = {"up": "aumentar o volume", "down": "diminuir o volume",
              "mute": "alternar o mudo"}

    def run():
        subprocess.run(cmd, capture_output=True, timeout=5, check=True)
        return f"Pronto, volume ajustado."

    return f"Vou {labels[direction]}", run


def _cmd_screenshot():
    pictures = Path.home() / "Pictures"
    target_dir = pictures if pictures.is_dir() else Path.home()
    target = target_dir / f"screenshot-{datetime.now():%Y%m%d-%H%M%S}.png"

    # Wayland (Hyprland, wlroots) primeiro; depois GNOME/KDE; X11 genérico no fim
    candidates = [
        ["hyprshot", "-m", "output", "-o", str(target_dir), "-f", target.name],
        ["grim", str(target)],
        ["gnome-screenshot", "-f", str(target)],
        ["spectacle", "-b", "-n", "-o", str(target)],
        ["maim", str(target)],
        ["scrot", str(target)],
        ["import", "-window", "root", str(target)],  # ImageMagick
    ]
    for cmd in candidates:
        if shutil.which(cmd[0]):
            break
    else:
        return ("Queria tirar um print, mas não achei ferramenta de captura",
                lambda: "Sem hyprshot, grim, gnome-screenshot, spectacle, "
                        "maim, scrot ou import instalados.")

    def run():
        subprocess.run(cmd, capture_output=True, timeout=15, check=True)
        return f"Print salvo em {target}."

    return "Vou tirar um print da tela", run


# ---------------------------------------------------------------------------
# Parser de intenções (ordem importa: URLs antes de apps)
# ---------------------------------------------------------------------------
_RE_URL = re.compile(
    r"abr(?:a|ir|e)\s+(?:o\s+|a\s+)?(?:site\s+|p[áa]gina\s+)?"
    r"((?:https?://)?[\w-]+(?:\.[\w-]+)+(?:/\S*)?)", re.IGNORECASE)
_RE_APP = re.compile(
    r"abr(?:a|ir|e)\s+(?:o\s+|a\s+)?"
    r"(chrome|firefox|vscode|spotify|terminal)\b", re.IGNORECASE)
_RE_VOLUME = re.compile(
    r"(aumenta|aumentar|sobe|subir|diminui|diminuir|abaixa|abaixar|desce|descer)"
    r"\s+(?:o\s+)?volume", re.IGNORECASE)
_RE_MUTE = re.compile(
    r"(muta|mutar|desmuta|desmutar|silencia|silenciar)(?:\s+(?:o\s+)?(?:audio|som))?",
    re.IGNORECASE)
_RE_SHOT = re.compile(
    r"(tir\w+\s+(?:um\s+|uma\s+)?(print|screenshot|foto da tela)|"
    r"captura(?:r)?\s+de\s+tela|print\s+da\s+tela)", re.IGNORECASE)


def parse_command(text: str):
    """Reconhece a intenção e devolve (descrição, ação) ou None.

    URLs só casam se tiverem pelo menos um ponto (evita tratar 'abrir a
    gaveta' como site).
    """
    if not text:
        return None
    t = text.lower().strip()

    m = _RE_VOLUME.search(t)
    if m:
        direction = "up" if m.group(1)[:4] in ("aume", "sobe", "subi") else "down"
        return _cmd_volume(direction)

    if _RE_MUTE.search(t):
        return _cmd_volume("mute")

    if _RE_SHOT.search(t):
        return _cmd_screenshot()

    m = _RE_URL.search(t)
    if m:
        return _cmd_open_url(m.group(1))

    m = _RE_APP.search(t)
    if m:
        return _cmd_open_app(m.group(1).lower())

    return None

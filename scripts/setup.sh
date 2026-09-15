#!/usr/bin/env bash
# =============================================================================
# Fyde Jarvis — Setup do voice-client (qualquer distro Linux)
#
# Detecta o gerenciador de pacotes (pacman, apt, dnf, zypper), instala as
# dependências de sistema, cria o venv, baixa a voz do Piper e prepara o .env.
#
# Uso:   bash scripts/setup.sh          (de qualquer pasta)
# Alvo:  CachyOS/Arch, Debian/Ubuntu, Fedora, openSUSE (glibc; Alpine não)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VC_DIR="$SCRIPT_DIR/../voice-client"
PIPER_VERSION="1.2.0"
VOICE_URL_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium"

info() { printf "\033[1;34m[setup]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[setup]\033[0m %s\n" "$*"; }
ok()   { printf "\033[1;32m[setup]\033[0m %s\n" "$*"; }

[ -d "$VC_DIR" ] || { echo "voice-client não encontrado em $VC_DIR"; exit 1; }
cd "$VC_DIR"

# ---------------------------------------------------------------------------
# 1. Dependências de sistema (portaudio + python venv + wget/curl)
# ---------------------------------------------------------------------------
SUDO=""
if [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi

install_packages() {
    if command -v pacman >/dev/null; then
        info "Arch/CachyOS detectado (pacman)"
        $SUDO pacman -S --needed --noconfirm portaudio python python-pip wget curl
    elif command -v apt-get >/dev/null; then
        info "Debian/Ubuntu detectado (apt)"
        $SUDO apt-get update
        $SUDO apt-get install -y portaudio19-dev python3 python3-venv python3-pip wget curl
    elif command -v dnf >/dev/null; then
        info "Fedora detectado (dnf)"
        $SUDO dnf install -y portaudio-devel python3 python3-pip wget curl
    elif command -v zypper >/dev/null; then
        info "openSUSE detectado (zypper)"
        $SUDO zypper --non-interactive install portaudio-devel python3 python3-pip wget curl
    else
        warn "Gerenciador de pacotes não reconhecido."
        warn "Instale manualmente: portaudio, python3+venv, wget/curl."
    fi
}

if ! command -v sudo >/dev/null && [ "$(id -u)" -ne 0 ]; then
    warn "sem sudo: pulando dependências de sistema (instale portaudio à mão)"
else
    install_packages
fi

# ---------------------------------------------------------------------------
# 2. Ambiente virtual + dependências Python
# ---------------------------------------------------------------------------
info "Criando venv e instalando requirements..."
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt
ok "Python pronto"

# ---------------------------------------------------------------------------
# 3. Piper TTS (binário) + voz pt_BR
# ---------------------------------------------------------------------------
if command -v piper >/dev/null 2>&1; then
    ok "piper já está no PATH"
else
    ARCH="$(uname -m)"
    case "$ARCH" in
        x86_64)  PKG="piper_amd64" ;;
        aarch64) PKG="piper_arm64" ;;
        *)       PKG="" ;;
    esac

    if [ -n "$PKG" ]; then
        info "Baixando Piper $PIPER_VERSION ($ARCH)..."
        TMP="$(mktemp -d)"
        if curl -fsSL "https://github.com/rhasspy/piper/releases/download/v${PIPER_VERSION}/${PKG}.tar.gz" -o "$TMP/piper.tar.gz"; then
            tar -xzf "$TMP/piper.tar.gz" -C "$TMP"
            mkdir -p "$HOME/.local/bin"
            cp "$TMP/piper/piper" "$HOME/.local/bin/piper"
            chmod +x "$HOME/.local/bin/piper"
            ok "piper instalado em ~/.local/bin/piper"
            case ":$PATH:" in
                *":$HOME/.local/bin:"*) ;;
                *) warn "Adicione ao PATH: export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
            esac
        else
            warn "Download falhou. Baixe manual em github.com/rhasspy/piper/releases"
        fi
        rm -rf "$TMP"
    else
        warn "Arquitetura $ARCH sem release oficial — veja github.com/rhasspy/piper/releases"
    fi
fi

mkdir -p models/piper
if [ ! -f "models/piper/pt_BR-faber-medium.onnx" ]; then
    info "Baixando voz pt_BR (faber/medium)..."
    (cd models/piper
     curl -fsSL -O "$VOICE_URL_BASE/pt_BR-faber-medium.onnx"
     curl -fsSL -O "$VOICE_URL_BASE/pt_BR-faber-medium.onnx.json")
    ok "voz pt_BR pronta"
else
    ok "voz pt_BR já existe"
fi

# ---------------------------------------------------------------------------
# 4. Configuração
# ---------------------------------------------------------------------------
if [ ! -f ".env" ]; then
    cp .env.example .env
    ok ".env criado a partir do .env.example"
else
    ok ".env já existe (mantido)"
fi

echo
ok "Setup concluído! 🎙️"
echo "  Para rodar:  cd voice-client && source .venv/bin/activate && python main.py"
echo "  E suba a API:  cd apps/api && uvicorn app.main:app --reload --port 8000"

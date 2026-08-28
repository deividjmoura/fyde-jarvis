# Voice Client – Fyde Jarvis

Cliente de voz local que usa o **cérebro** (API do fyde-jarvis).

## Instalação rápida (CachyOS / Arch)

```bash
sudo pacman -S --needed portaudio python-pip python-virtualenv
paru -S piper-tts   # ou instale o binário manualmente

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Voz pt_BR
mkdir -p models/piper && cd models/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json
cd ../..

cp .env.example .env
# JARVIS_API_URL=http://localhost:8000
```

## Rodar

1. Suba a API do fyde-jarvis na porta 8000.
2. Neste diretório:

```bash
source .venv/bin/activate
python main.py
```

Diga **"sair"** ou pressione `Ctrl+C` para encerrar.

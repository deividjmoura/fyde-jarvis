# Voice Client – Fyde Jarvis

Cliente de voz local que usa o **cérebro** (API do fyde-jarvis).

```
"Jarvis" 🎙️ → openWakeWord (local) → "Sim?"
   → sua pergunta (Whisper, local)
   → API /agent/chat-test-stream (cérebro na nuvem)
   → Piper fala a resposta frase a frase, em tempo real
```

## Instalação rápida (CachyOS / Arch)

```bash
sudo pacman -S --needed portaudio python-pip python-virtualenv
paru -S piper-tts   # ou instale o binário manualmente

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # inclui openwakeword (modelos embutidos)

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

## Modos de operação

| Modo | Como funciona | Como ativar |
|------|---------------|-------------|
| **Wake word** (padrão) | Assistente **dorme** até ouvir **"Jarvis"**, responde "Sim?", conversa e volta a dormir | `WAKE_WORD_ENABLED=true` |
| **Contínuo** | Escuta em loop (comportamento clássico) | `WAKE_WORD_ENABLED=false` |

> A wake word usa `openwakeword` (modelo `hey_jarvis` embutido, 100% local —
> nenhum áudio sai da sua máquina até você chamá-lo). Se a lib falhar, o
> cliente **cai para o modo contínuo automaticamente**.

Ajuste no `.env` se houver falsos positivos/negativos:

```env
WAKE_WORD_THRESHOLD=0.5   # ↑ mais estrito (menos falsos positivos)
WAKE_WORD_COOLDOWN=2.0    # segundos entre detecções
```

Diga **"sair"** ou pressione `Ctrl+C` para encerrar.

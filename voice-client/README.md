# Voice Client – Fyde Jarvis

Cliente de voz local que usa o **cérebro** (API do fyde-jarvis).

```
"Jarvis" 🎙️ → openWakeWord (local) → "Sim?"
   → sua pergunta (Whisper, local)
   → API /agent/chat-test-stream (cérebro na nuvem)
   → Piper fala a resposta frase a frase, em tempo real
```

## Instalação — qualquer distro

### Opção 1: script automático (recomendado)

```bash
bash scripts/setup.sh   # a partir da raiz do repo; detecta sua distro
```

### Opção 2: manual por gerenciador de pacotes

| Distro | Dependências de sistema |
|---|---|
| **CachyOS / Arch** | `sudo pacman -S --needed portaudio python python-pip wget curl` |
| **Debian / Ubuntu** | `sudo apt install portaudio19-dev python3-venv python3-pip wget curl` |
| **Fedora** | `sudo dnf install portaudio-devel python3 python3-pip wget curl` |
| **openSUSE** | `sudo zypper install portaudio-devel python3 python3-pip wget curl` |

Depois, em qualquer uma delas:

```bash
cd voice-client
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # inclui openwakeword (modelos embutidos)

# Voz pt_BR
mkdir -p models/piper && cd models/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json
cd ../..

cp .env.example .env
# JARVIS_API_URL=http://localhost:8000
```

### Piper TTS (binário)

- **Arch:** `paru -S piper-tts` · **outras:** o `setup.sh` baixa o release oficial
  para `~/.local/bin` (x86_64/aarch64), ou baixe manual em
  [github.com/rhasspy/piper/releases](https://github.com/rhasspy/piper/releases).

### Notas de compatibilidade

- **Wayland** (Hyprland, Sway, GNOME Wayland): screenshots usam `hyprshot`/`grim`
  automaticamente antes das ferramentas X11.
- **Apps via Flatpak**: se o binário nativo não existir, comandos como
  "abre o spotify" tentam `flatpak run <id>` automaticamente.
- **Áudio**: `pactl` (PipeWire/PulseAudio) com fallback `amixer` (ALSA).
- **Alpine/musl**: não suportado oficialmente (onnxruntime/faster-whisper
  exigem glibc) — use o container da API + uma distro glibc para voz.
- **API em qualquer SO**: `docker compose --profile full up --build` sobe
  Postgres + API sem instalar nada além do Docker.

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

## 🖥️ Comandos de PC (com confirmação verbal)

Além de conversar com o cérebro, o Jarvis executa ações locais — **sempre
pedindo confirmação antes** ("Posso executar?" → só roda com "sim/pode/bora..."):

| Você fala | Ele faz |
|---|---|
| "abre o google.com" / "abrir site github.com" | Abre a URL no navegador |
| "abre o chrome / firefox / vscode / spotify / terminal" | Lança o app |
| "aumenta o volume" / "diminui o volume" / "muta" | Ajusta o áudio (pactl/amixer) |
| "tira um print" | Screenshot em `~/Pictures` |

Frases que não casam seguem normalmente para o cérebro. Padrão seguro:
**resposta ambígua = cancela**. Apps e executáveis em
`system_commands.KNOWN_APPS`; testes em `tests/` (42 casos).

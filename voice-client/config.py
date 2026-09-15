"""
Configurações do cliente de voz do Fyde Jarvis.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
PIPER_DIR = MODELS_DIR / "piper"

# === API do cérebro (fyde-jarvis) ===
JARVIS_API_URL = os.getenv("JARVIS_API_URL", "http://localhost:8000")
# Usa o endpoint sem auth para o modo pessoal
CHAT_ENDPOINT = f"{JARVIS_API_URL.rstrip('/')}/agent/chat-test"

# === Áudio ===
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"
RECORD_SECONDS = 8
SILENCE_THRESHOLD = 0.01
SILENCE_DURATION = 1.2
INPUT_DEVICE = None  # None = padrão do sistema

# === STT (faster-whisper) ===
WHISPER_MODEL = "base"       # tiny | base | small | medium
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_LANGUAGE = "pt"

# === TTS (Piper) ===
PIPER_MODEL = PIPER_DIR / "pt_BR-faber-medium.onnx"
PIPER_CONFIG = PIPER_DIR / "pt_BR-faber-medium.onnx.json"
PIPER_BINARY = "piper"

# === Wake word (openWakeWord, modelo pré-treinado "hey_jarvis") ===
WAKE_WORD_ENABLED = os.getenv("WAKE_WORD_ENABLED", "true").lower() == "true"
WAKE_WORD_MODEL = os.getenv("WAKE_WORD_MODEL", "hey_jarvis")
WAKE_WORD_THRESHOLD = float(os.getenv("WAKE_WORD_THRESHOLD", "0.5"))
WAKE_WORD_COOLDOWN = float(os.getenv("WAKE_WORD_COOLDOWN", "2.0"))  # segundos

"""Text-to-Speech com Piper (binário local)."""

import subprocess
import tempfile
import os
import sounddevice as sd
import soundfile as sf
from pathlib import Path
import config


class TextToSpeech:
    def __init__(self):
        self.model_path = Path(config.PIPER_MODEL)
        self.config_path = Path(config.PIPER_CONFIG)
        self.binary = config.PIPER_BINARY

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Modelo Piper não encontrado: {self.model_path}\n"
                "Baixe a voz pt_BR (veja README do voice-client)."
            )

        try:
            subprocess.run([self.binary, "--help"], capture_output=True, check=False)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Binário '{self.binary}' não está no PATH.\n"
                "Instale piper-tts ou coloque o binário no PATH."
            )
        print("[TTS] Piper pronto.")

    def speak(self, text: str):
        if not text or not text.strip():
            return
        text = text.strip()
        print(f"[TTS] {text[:90]}{'...' if len(text) > 90 else ''}")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        try:
            cmd = [
                self.binary,
                "--model", str(self.model_path),
                "--output_file", wav_path,
            ]
            if self.config_path.exists():
                cmd.extend(["--config", str(self.config_path)])

            subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                check=True,
            )
            data, sr = sf.read(wav_path, dtype="float32")
            sd.play(data, sr)
            sd.wait()
        except subprocess.CalledProcessError as e:
            print(f"[TTS] Erro Piper: {e.stderr.decode(errors='ignore')}")
        finally:
            if os.path.exists(wav_path):
                os.unlink(wav_path)

#!/usr/bin/env python3
"""
Fyde Jarvis – Cliente de voz local
Fala → Whisper → API (cérebro) → Piper
"""

import sys
import signal
from audio import record_until_silence
from stt import SpeechToText
from tts import TextToSpeech
from api_client import JarvisAPI
import config


def signal_handler(sig, frame):
    print("\n\nEncerrando. Até logo!")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 52)
    print("  FYDE JARVIS – Cliente de Voz (híbrido)")
    print("=" * 52)
    print(f"API  : {config.JARVIS_API_URL}")
    print(f"STT  : Whisper '{config.WHISPER_MODEL}'")
    print(f"TTS  : Piper")
    print("-" * 52)
    print("Fale após 'Escutando...'  |  Ctrl+C para sair")
    print("-" * 52)

    try:
        stt = SpeechToText()
        tts = TextToSpeech()
        brain = JarvisAPI()
    except Exception as e:
        print(f"\n❌ Erro na inicialização:\n{e}")
        sys.exit(1)

    tts.speak("Olá. Estou online e conectado ao cérebro. Como posso ajudar?")

    while True:
        try:
            audio = record_until_silence()

            if len(audio) < config.SAMPLE_RATE * 0.3:
                print("... silêncio demais, tentando de novo.")
                continue

            print("[STT] Transcrevendo...")
            text = stt.transcribe(audio)

            if not text:
                print("Não entendi.")
                tts.speak("Não entendi. Pode repetir?")
                continue

            print(f"Você: {text}")

            if text.lower().strip() in ("sair", "tchau", "encerrar", "desligar"):
                tts.speak("Até logo!")
                break

            print("[API] Consultando o cérebro...")
            response = brain.chat(text)
            print(f"Jarvis: {response}")

            tts.speak(response)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n⚠️  Erro: {e}")
            tts.speak("Desculpe, ocorreu um erro. Tente novamente.")

    print("\nCliente de voz desligado.")


if __name__ == "__main__":
    main()

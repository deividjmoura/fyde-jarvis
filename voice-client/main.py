#!/usr/bin/env python3
"""
Fyde Jarvis – Cliente de voz local
Wake word "Jarvis" → Whisper → API (cérebro, com streaming) → Piper

Modos de operação:
- Wake word (padrão): assistente dorme até ouvir "Jarvis".
- Contínuo: escuta em loop (fallback se openwakeword não estiver disponível,
  ou WAKE_WORD_ENABLED=false no .env).
"""

import sys
import signal

from audio import record_until_silence
from stt import SpeechToText
from tts import TextToSpeech
from api_client import JarvisAPI
import config

EXIT_WORDS = ("sair", "tchau", "encerrar", "desligar")


def signal_handler(sig, frame):
    print("\n\nEncerrando. Até logo!")
    sys.exit(0)


def process_utterance(stt, tts, brain) -> bool:
    """Uma rodada de conversa: grava → STT → cérebro (stream) → TTS.

    Retorna False se o usuário pediu para sair.
    """
    audio = record_until_silence()

    if len(audio) < config.SAMPLE_RATE * 0.3:
        print("... silêncio demais, tentando de novo.")
        return True

    print("[STT] Transcrevendo...")
    text = stt.transcribe(audio)

    if not text:
        print("Não entendi.")
        tts.speak("Não entendi. Pode repetir?")
        return True

    print(f"Você: {text}")

    if text.lower().strip() in EXIT_WORDS:
        tts.speak("Até logo!")
        return False

    print("[API] Consultando o cérebro (streaming)...")
    try:
        full_response = ""
        for sentence in brain.chat_stream(text):
            print(f"Jarvis: {sentence}")
            tts.speak(sentence)
            full_response += (" " if full_response else "") + sentence

        if not full_response:
            response = brain.chat(text)
            print(f"Jarvis: {response}")
            tts.speak(response)

    except Exception as stream_err:
        # API sem endpoint de streaming: modo clássico.
        print(f"[API] Streaming indisponível ({stream_err}). Modo clássico.")
        response = brain.chat(text)
        print(f"Jarvis: {response}")
        tts.speak(response)

    return True


def run_wakeword_mode(stt, tts, brain, detector):
    """Dorme até ouvir 'Jarvis', conversa, volta a dormir."""
    print(f"🎧 Diga '{config.WAKE_WORD_MODEL.replace('hey_', '').title()}' "
          "para me chamar. Ctrl+C para sair.")
    tts.speak("Sistema pronto. Me chame pelo nome quando precisar.")

    while True:
        detector.wait_for_wakeword()
        print("👂 Wake word detectada!")
        tts.speak("Sim?")

        keep_going = process_utterance(stt, tts, brain)
        if not keep_going:
            break

        print("🎧 Voltando a dormir. Me chame pelo nome...")
        print("-" * 52)


def run_continuous_mode(stt, tts, brain):
    """Loop clássico: escuta → responde → escuta."""
    print("Fale após 'Escutando...'  |  Ctrl+C para sair")
    print("-" * 52)
    tts.speak("Olá. Estou online e conectado ao cérebro. Como posso ajudar?")

    while True:
        if not process_utterance(stt, tts, brain):
            break


def main():
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 52)
    print("  FYDE JARVIS – Cliente de Voz (híbrido)")
    print("=" * 52)
    print(f"API  : {config.JARVIS_API_URL}")
    print(f"STT  : Whisper '{config.WHISPER_MODEL}'")
    print(f"TTS  : Piper")
    print(f"WAKE : {'on (' + config.WAKE_WORD_MODEL + ')' if config.WAKE_WORD_ENABLED else 'off'}")
    print("-" * 52)

    try:
        stt = SpeechToText()
        tts = TextToSpeech()
        brain = JarvisAPI()
    except Exception as e:
        print(f"\n❌ Erro na inicialização:\n{e}")
        sys.exit(1)

    # Wake word é o padrão, mas nunca quebra a experiência:
    # qualquer problema → modo contínuo.
    detector = None
    if config.WAKE_WORD_ENABLED:
        try:
            from wakeword import WakeWordDetector
            detector = WakeWordDetector()
        except Exception as e:
            print(f"[WAKE] Indisponível: {e}")
            print("[WAKE] Seguindo em modo contínuo.")

    try:
        if detector:
            run_wakeword_mode(stt, tts, brain, detector)
        else:
            run_continuous_mode(stt, tts, brain)
    except KeyboardInterrupt:
        pass

    print("\nCliente de voz desligado.")


if __name__ == "__main__":
    main()

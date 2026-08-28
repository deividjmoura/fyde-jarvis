"""Speech-to-Text com faster-whisper (local)."""

from faster_whisper import WhisperModel
import numpy as np
import config


class SpeechToText:
    def __init__(self):
        print(f"[STT] Carregando Whisper '{config.WHISPER_MODEL}'...")
        self.model = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )
        print("[STT] Pronto.")

    def transcribe(self, audio: np.ndarray) -> str:
        if audio is None or len(audio) == 0:
            return ""
        segments, _ = self.model.transcribe(
            audio,
            language=config.WHISPER_LANGUAGE,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        return " ".join(s.text.strip() for s in segments).strip()

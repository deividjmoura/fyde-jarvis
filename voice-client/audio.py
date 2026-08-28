"""Captura de microfone com detecção de silêncio."""

import sounddevice as sd
import numpy as np
import time
import config


def list_devices():
    print(sd.query_devices())


def record_until_silence(
    max_seconds: float = None,
    silence_threshold: float = None,
    silence_duration: float = None,
) -> np.ndarray:
    max_seconds = max_seconds or config.RECORD_SECONDS
    silence_threshold = silence_threshold or config.SILENCE_THRESHOLD
    silence_duration = silence_duration or config.SILENCE_DURATION

    sample_rate = config.SAMPLE_RATE
    chunk_duration = 0.1
    chunk_samples = int(sample_rate * chunk_duration)
    max_chunks = int(max_seconds / chunk_duration)
    required_silent = int(silence_duration / chunk_duration)

    frames = []
    silent_chunks = 0

    def callback(indata, frames_count, time_info, status):
        if status:
            print(f"[Áudio] {status}")
        frames.append(indata.copy())

    print("🎤 Escutando... (fale agora)")

    with sd.InputStream(
        samplerate=sample_rate,
        channels=config.CHANNELS,
        dtype=config.DTYPE,
        blocksize=chunk_samples,
        device=config.INPUT_DEVICE,
        callback=callback,
    ):
        started = False
        for _ in range(max_chunks):
            time.sleep(chunk_duration)
            if not frames:
                continue
            volume = np.abs(frames[-1]).mean()
            if volume > silence_threshold:
                started = True
                silent_chunks = 0
            elif started:
                silent_chunks += 1
                if silent_chunks >= required_silent:
                    break

    if not frames:
        return np.array([], dtype=np.float32)
    return np.concatenate(frames, axis=0).flatten().astype(np.float32)

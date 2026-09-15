"""
Detecção de wake word "Jarvis" com openWakeWord (100% local).

Usa o modelo pré-treinado `hey_jarvis` (openWakeWord). Se a lib ou o
modelo não estiverem disponíveis, levanta exceção na construção —
o main.py cai para o modo contínuo (sem wake word) automaticamente.
"""

import time

import numpy as np

import config

CHUNK_SAMPLES = 1280  # 80 ms @ 16 kHz (tamanho recomendado pelo openWakeWord)


class WakeWordDetector:
    def __init__(self):
        try:
            import openwakeword
            from openwakeword.model import Model
        except ImportError as e:
            raise RuntimeError(
                "openwakeword não instalado. Rode: pip install openwakeword"
            ) from e

        self.model = self._load_model(openwakeword, Model)

        self._last_trigger = 0.0
        print(f"[WAKE] Modelo '{config.WAKE_WORD_MODEL}' pronto "
              f"(limiar {config.WAKE_WORD_THRESHOLD}).")

    @staticmethod
    def _load_model(openwakeword, Model):
        """Carrega o modelo sendo compatível com várias versões do openWakeWord.

        - >= 0.6: aceita `wakeword_models=["hey_jarvis"]` (baixa se preciso)
        - 0.4/0.5: aceita `wakeword_model_paths=[caminho]` — os modelos vêm
          embutidos no pacote em resources/models/
        """
        name = config.WAKE_WORD_MODEL

        # API nova (>= 0.6)
        try:
            return Model(wakeword_models=[name])
        except TypeError:
            pass
        except Exception:
            # modelo não encontrado/baixado — tenta download (só existe na >= 0.6)
            try:
                from openwakeword.utils import download_models
                download_models(model_names=[name])
                return Model(wakeword_models=[name])
            except Exception:
                pass

        # API antiga (0.4/0.5): caminho do recurso embutido no pacote
        from pathlib import Path
        candidate = (
            Path(openwakeword.__file__).parent
            / "resources" / "models" / f"{name}_v0.1.onnx"
        )
        if candidate.exists():
            return Model(wakeword_model_paths=[str(candidate)])

        raise RuntimeError(
            f"Não consegui carregar o modelo '{name}'. "
            f"Procurei em: API nova (por nome) e {candidate}"
        )

    def wait_for_wakeword(self):
        """Bloqueia até ouvir a wake word. Retorna True ao detectar."""
        import sounddevice as sd

        with sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
            dtype="int16",
            blocksize=CHUNK_SAMPLES,
            device=config.INPUT_DEVICE,
        ) as stream:
            while True:
                chunk, _ = stream.read(CHUNK_SAMPLES)
                scores = self.model.predict(chunk.flatten())

                score = max(scores.values()) if scores else 0.0
                if score < config.WAKE_WORD_THRESHOLD:
                    continue

                # Debounce: evita múltiplos disparos na mesma fala
                now = time.time()
                if now - self._last_trigger >= config.WAKE_WORD_COOLDOWN:
                    self._last_trigger = now
                    if hasattr(self.model, "reset"):
                        self.model.reset()
                    return True

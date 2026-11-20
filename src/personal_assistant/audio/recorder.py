from __future__ import annotations

import numpy as np
import sounddevice as sd


def record(seconds: float, sample_rate: int = 16_000) -> np.ndarray:
    """Record mono audio from the default microphone as float32 in [-1, 1]."""
    frames = int(seconds * sample_rate)
    audio = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    return audio.reshape(-1)

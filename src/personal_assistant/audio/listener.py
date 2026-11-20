"""Always-on microphone stream. Frames are pushed to a callback from PortAudio's thread."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


class Microphone:
    def __init__(self, on_frame: Callable[[np.ndarray], None], sample_rate=16_000, frame_ms=30):
        import sounddevice as sd

        self._stream = sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            blocksize=sample_rate * frame_ms // 1000,
            callback=lambda data, _frames, _time, _status: on_frame(data[:, 0].copy()),
        )

    def start(self) -> None:
        self._stream.start()

    def stop(self) -> None:
        self._stream.stop()
        self._stream.close()

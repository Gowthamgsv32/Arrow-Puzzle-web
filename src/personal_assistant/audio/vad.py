"""Energy-based voice activity detection that splits a continuous mic stream into
utterances. Pure numpy, so it is cheap enough to run on every 30 ms frame."""

from __future__ import annotations

from collections import deque

import numpy as np


def rms(frame: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(frame, dtype=np.float64)))) if frame.size else 0.0


class UtteranceSegmenter:
    """Feed fixed-size frames; get back a whole utterance once the speaker pauses.

    The speech threshold adapts to background noise: it is ``noise_floor * ratio``
    but never below ``min_rms``. A short pre-roll keeps the first syllable.
    """

    def __init__(
        self,
        sample_rate: int = 16_000,
        frame_ms: int = 30,
        min_rms: float = 0.010,
        ratio: float = 3.0,
        silence_ms: int = 700,
        min_speech_ms: int = 250,
        max_seconds: float = 15.0,
        pre_roll_ms: int = 300,
    ):
        self.frame_ms = frame_ms
        self.min_rms = min_rms
        self.ratio = ratio
        self.silence_frames = max(1, silence_ms // frame_ms)
        self.min_speech_frames = max(1, min_speech_ms // frame_ms)
        self.max_frames = int(max_seconds * 1000 // frame_ms)
        self.pre_roll: deque[np.ndarray] = deque(maxlen=max(1, pre_roll_ms // frame_ms))
        self.noise_floor = min_rms / ratio
        self.reset()

    @property
    def threshold(self) -> float:
        return max(self.min_rms, self.noise_floor * self.ratio)

    @property
    def in_speech(self) -> bool:
        return self._active

    def reset(self) -> None:
        self._active = False
        self._frames: list[np.ndarray] = []
        self._speech = 0
        self._silence = 0
        self.pre_roll.clear()

    def feed(self, frame: np.ndarray) -> np.ndarray | None:
        level = rms(frame)
        loud = level >= self.threshold
        if not self._active:
            if loud:
                self._active = True
                self._frames = [*self.pre_roll, frame]
                self._speech, self._silence = 1, 0
            else:
                # Slowly track background noise only while nobody is talking.
                self.noise_floor = 0.95 * self.noise_floor + 0.05 * level
                self.pre_roll.append(frame)
            return None

        self._frames.append(frame)
        # Hysteresis: once talking, a slightly quieter frame still counts as speech.
        if level >= self.threshold * 0.6:
            self._speech += 1
            self._silence = 0
        else:
            self._silence += 1

        if self._silence >= self.silence_frames or len(self._frames) >= self.max_frames:
            frames, speech = self._frames, self._speech
            self.reset()
            if speech >= self.min_speech_frames:
                return np.concatenate(frames)
        return None

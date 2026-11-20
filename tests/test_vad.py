import numpy as np

from personal_assistant.audio.vad import UtteranceSegmenter

SR = 16_000
FRAME = SR * 30 // 1000


def frames(seconds: float, amplitude: float, seed: int = 0):
    rng = np.random.default_rng(seed)
    n = int(seconds * 1000 / 30)
    for _ in range(n):
        yield (rng.standard_normal(FRAME) * amplitude).astype(np.float32)


def feed(seg, stream):
    return [u for f in stream if (u := seg.feed(f)) is not None]


def test_speech_between_silence_is_one_utterance():
    seg = UtteranceSegmenter(silence_ms=600)
    stream = [*frames(1.0, 0.001), *frames(1.2, 0.08, 1), *frames(1.0, 0.001, 2)]
    out = feed(seg, stream)
    assert len(out) == 1
    # speech + pre-roll + trailing silence
    assert 1.2 <= len(out[0]) / SR <= 2.2


def test_two_sentences_with_pause_are_split():
    seg = UtteranceSegmenter(silence_ms=500)
    stream = [
        *frames(0.5, 0.001),
        *frames(0.8, 0.08, 1),
        *frames(1.0, 0.001, 2),
        *frames(0.8, 0.08, 3),
        *frames(1.0, 0.001, 4),
    ]
    assert len(feed(seg, stream)) == 2


def test_short_click_is_ignored():
    seg = UtteranceSegmenter(min_speech_ms=250)
    stream = [*frames(0.5, 0.001), *frames(0.06, 0.2, 1), *frames(1.0, 0.001, 2)]
    assert feed(seg, stream) == []


def test_background_noise_raises_threshold():
    seg = UtteranceSegmenter(min_rms=0.005)
    # steady fan noise slightly above min_rms should not trigger after adapting
    assert feed(seg, frames(0.3, 0.001)) == []
    seg.noise_floor = 0.004
    assert seg.threshold > 0.005
    assert feed(seg, frames(2.0, 0.0035, 5)) == []


def test_long_speech_is_capped():
    seg = UtteranceSegmenter(max_seconds=2.0)
    out = feed(seg, [*frames(0.3, 0.001), *frames(5.0, 0.08, 1)])
    assert len(out) >= 2
    assert all(len(u) / SR <= 2.1 for u in out)

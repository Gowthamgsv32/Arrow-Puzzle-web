"""Text-to-speech using Microsoft Edge neural voices (edge-tts).

Good Tamil voices (ta-IN-PallaviNeural, ta-IN-ValluvarNeural). Requires internet.
Swap this class for an offline engine later if needed.
"""

from __future__ import annotations

import asyncio
import io


class TextToSpeech:
    def speak(self, text: str, voice: str) -> None:
        import sounddevice as sd
        import soundfile as sf

        mp3 = asyncio.run(self._synthesize(text, voice))
        data, sample_rate = sf.read(io.BytesIO(mp3))
        sd.play(data, sample_rate)
        sd.wait()

    @staticmethod
    async def _synthesize(text: str, voice: str) -> bytes:
        import edge_tts

        buf = io.BytesIO()
        async for chunk in edge_tts.Communicate(text, voice).stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        return buf.getvalue()

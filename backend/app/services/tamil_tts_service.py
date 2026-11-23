import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import edge_tts
from app.core.config import settings

logger = logging.getLogger("TamilKidsAI.TTSService")

class TamilTTSService:
    def __init__(
        self,
        voice: str = settings.TAMIL_TTS_VOICE,
        rate: str = settings.TTS_RATE,
        pitch: str = settings.TTS_PITCH
    ):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    async def generate_speech_with_subtitles(
        self,
        text: str,
        output_audio_path: str,
        output_srt_path: str
    ) -> Dict[str, any]:
        """
        Synthesizes Tamil speech using edge-tts neural voice,
        extracts word/sentence timings, and writes both MP3 audio and SRT subtitles.
        """
        output_audio_file = Path(output_audio_path)
        output_srt_file = Path(output_srt_path)
        output_audio_file.parent.mkdir(parents=True, exist_ok=True)
        output_srt_file.parent.mkdir(parents=True, exist_ok=True)

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch
        )

        sub_maker = edge_tts.SubMaker()
        
        with open(output_audio_path, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    sub_maker.feed(chunk)

        # Write SRT subtitle file
        srt_content = sub_maker.get_srt()
        with open(output_srt_path, "w", encoding="utf-8") as srt_file:
            srt_file.write(srt_content)

        logger.info(f"Generated Tamil narration: {output_audio_path} and subtitles: {output_srt_path}")
        
        return {
            "audio_path": str(output_audio_path),
            "srt_path": str(output_srt_path),
            "voice": self.voice
        }

    def generate_sync(self, text: str, output_audio_path: str, output_srt_path: str) -> Dict[str, any]:
        """Synchronous wrapper for FastAPI and background workers"""
        return asyncio.run(self.generate_speech_with_subtitles(text, output_audio_path, output_srt_path))

    @staticmethod
    def get_available_tamil_voices() -> List[Dict[str, str]]:
        return [
            {
                "id": "ta-IN-PallaviNeural",
                "name": "Pallavi (பெண் குரல் - அன்பான கதை சொல்லும் குரல்)",
                "gender": "Female",
                "locale": "ta-IN"
            },
            {
                "id": "ta-IN-ValluvarNeural",
                "name": "Valluvar (ஆண் குரல் - தெளிவான கம்பீர குரல்)",
                "gender": "Male",
                "locale": "ta-IN"
            },
            {
                "id": "ta-LK-KumarNeural",
                "name": "Kumar (ஆண் குரல் - இலங்கை தமிழ்)",
                "gender": "Male",
                "locale": "ta-LK"
            },
            {
                "id": "ta-LK-SaranyaNeural",
                "name": "Saranya (பெண் குரல் - இலங்கை தமிழ்)",
                "gender": "Female",
                "locale": "ta-LK"
            }
        ]

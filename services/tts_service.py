"""Text-to-Speech service using OpenAI TTS API."""

import base64
import os
from typing import Optional

from openai import AsyncOpenAI

from utils.logging_config import get_logger

logger = get_logger(__name__)


class TTSService:
    """Service for generating audio from text using OpenAI TTS."""

    AVAILABLE_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize TTS service.

        Args:
            openai_api_key: OpenAI API key (if not provided, reads from env)
        """
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be provided or set in environment")

        self.client = AsyncOpenAI(api_key=api_key)
        logger.info("TTS service initialized")

    async def generate_audio(self, text: str, voice: str = "nova") -> bytes:
        """
        Generate audio from text.

        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)

        Returns:
            Audio bytes in MP3 format

        Raises:
            ValueError: If voice is invalid
        """
        if voice not in self.AVAILABLE_VOICES:
            logger.warning(f"Invalid voice '{voice}', using 'nova' as fallback")
            voice = "nova"

        try:
            logger.info(f"Generating audio with voice '{voice}' (text length: {len(text)})")

            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
            )

            audio_bytes = response.content
            logger.info(f"Audio generated successfully (size: {len(audio_bytes)} bytes)")
            return audio_bytes

        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            raise

    async def generate_audio_base64(self, text: str, voice: str = "nova") -> str:
        """
        Generate audio and return as base64 string.

        Args:
            text: Text to convert to speech
            voice: Voice to use

        Returns:
            Base64-encoded audio string
        """
        audio_bytes = await self.generate_audio(text, voice)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        return audio_base64

    def should_generate_audio(self, text_audio_ratio: float) -> bool:
        """
        Determine if audio should be generated based on configuration.

        Args:
            text_audio_ratio: Ratio value (0-100)
                0-49: Text only
                50-100: Text + Audio

        Returns:
            True if audio should be generated
        """
        return text_audio_ratio >= 50


# Global instance (will be initialized in app.py)
tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get the global TTS service instance."""
    global tts_service
    if tts_service is None:
        tts_service = TTSService()
    return tts_service

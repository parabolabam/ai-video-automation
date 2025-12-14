import logging
from typing import Any

from features.audio.tts import generate_voiceover

logger = logging.getLogger(__name__)

class AudioService:
    """Service for audio generation (TTS)."""
    
    def __init__(self, openai_client: Any):
        self.openai_client = openai_client
        
    async def generate_voiceover(self, script: str) -> str:
        """Generate voiceover audio from script."""
        logger.info("Generating voiceover audio...")
        try:
            audio_path = await generate_voiceover(
                script,
                self.openai_client,
            )
            logger.info(f"Voiceover generated: {audio_path}")
            return audio_path
        except Exception as e:
            logger.error(f"Voiceover generation failed: {e}")
            raise

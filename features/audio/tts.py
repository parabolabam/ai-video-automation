#!/usr/bin/env python3
"""
Text-to-Speech generation using OpenAI TTS API.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Available voices: alloy, echo, fable, onyx, nova, shimmer
DEFAULT_VOICE = "nova"  # Energetic, good for viral content
DEFAULT_MODEL = "tts-1-hd"  # High quality


async def generate_voiceover(
    script: str,
    openai_client: Optional[AsyncOpenAI] = None,
    voice: Optional[str] = None,
    model: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    """Generate voiceover audio from script using OpenAI TTS.
    
    Args:
        script: The text to convert to speech
        openai_client: OpenAI async client (creates one if not provided)
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        model: TTS model (tts-1 or tts-1-hd)
        output_path: Path to save audio file (auto-generated if not provided)
        
    Returns:
        Path to the generated audio file (MP3)
        
    Raises:
        RuntimeError: If TTS generation fails
    """
    # Use environment variables or defaults
    voice = voice or os.getenv("TTS_VOICE", DEFAULT_VOICE)
    model = model or os.getenv("TTS_MODEL", DEFAULT_MODEL)
    
    # Create client if not provided
    if openai_client is None:
        openai_client = AsyncOpenAI()
    
    logger.info(f"Generating voiceover with voice={voice}, model={model}")
    logger.info(f"Script ({len(script)} chars): {script[:100]}...")
    
    try:
        response = await openai_client.audio.speech.create(
            model=model,
            voice=voice,
            input=script,
            response_format="mp3",
        )
        
        # Determine output path
        if output_path is None:
            # Create temp file in data directory
            data_dir = Path(os.getenv("DATA_DIR", "/data"))
            data_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(data_dir / f"voiceover_{os.getpid()}.mp3")
        
        # Save audio to file
        with open(output_path, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
        
        logger.info(f"Voiceover saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to generate voiceover: {e}")
        raise RuntimeError(f"TTS generation failed: {e}") from e


async def estimate_speech_duration(text: str, words_per_minute: int = 150) -> float:
    """Estimate how long the speech will take.
    
    Args:
        text: The text to speak
        words_per_minute: Speaking rate (default 150 WPM)
        
    Returns:
        Estimated duration in seconds
    """
    word_count = len(text.split())
    return (word_count / words_per_minute) * 60

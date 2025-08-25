#!/usr/bin/env python3
"""
Initialize API clients used by the pipeline
"""

import logging
import os
from typing import Dict, Any
import openai
from features.youtube.get_youtube_service import get_youtube_service
from features.blotato.client import BlotatoClient


def setup_apis() -> Dict[str, Any]:
    """Initialize API clients and return them in a dict."""
    logger = logging.getLogger(__name__)

    try:
        openai_client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        youtube_service = get_youtube_service()
        blotato_api_key = os.getenv("BLOTATO_API_KEY")
        blotato_client = (
            BlotatoClient(api_key=blotato_api_key) if blotato_api_key else None
        )
        logger.info("API clients initialized successfully (OpenAI, YouTube, Blotato)")
        return {
            "openai_client": openai_client,
            "youtube_service": youtube_service,
            "blotato_client": blotato_client,
        }
    except Exception as e:
        logger.error(f"Failed to initialize API clients: {e}")
        raise

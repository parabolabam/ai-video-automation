#!/usr/bin/env python3
"""
Initialize API clients used by the pipeline
"""

import logging
import os
from typing import Dict, Any
import openai
from features.youtube.get_youtube_service import get_youtube_service


def setup_apis() -> Dict[str, Any]:
    """Initialize API clients and return them in a dict."""
    logger = logging.getLogger(__name__)

    try:
        openai_client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        youtube_service = get_youtube_service()
        logger.info("API clients initialized successfully (OpenAI, YouTube)")
        return {
            "openai_client": openai_client,
            "youtube_service": youtube_service,
        }
    except Exception as e:
        logger.error(f"Failed to initialize API clients: {e}")
        raise

#!/usr/bin/env python3
"""
Create a demo placeholder file (used when video generation isn't available)
"""

import aiofiles
import logging
import os
import tempfile
from datetime import datetime
from typing import Optional


async def create_demo_placeholder(prompt: str) -> Optional[str]:
    """Create a placeholder text file and return None (no video)."""
    logger = logging.getLogger(__name__)
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        placeholder_file = f"video_placeholder_{timestamp}.txt"
        placeholder_path = os.path.join(tempfile.gettempdir(), placeholder_file)
        content = f"""AI Video Automation - Placeholder File

This file represents where a generated video would be placed.

Prompt: {prompt}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Expected Video: 8-second vertical (9:16) MP4

Status: Video generation not available via API yet.

To complete the pipeline:
1. Generate video manually using Google AI Studio
2. Replace this file with actual video: veo3_video_{timestamp}.mp4
3. Re-run the pipeline for YouTube upload

Alternative workflow:
- Use the manual instructions file generated
- Or integrate with other video APIs (RunwayML, Pika, etc.)
"""
        async with aiofiles.open(placeholder_path, 'w') as f:
            await f.write(content)
        logger.info(f"Demo placeholder created: {placeholder_path}")
        logger.warning("This is a placeholder - no actual video was generated")
        return None
    except Exception as e:
        logger.error(f"Failed to create placeholder: {e}")
        return None

#!/usr/bin/env python3
"""
Save binary video data to a temp file
"""

import aiofiles
import logging
import os
import tempfile
from datetime import datetime
from typing import Optional


async def save_video_data(video_data: bytes, custom_path: str | None = None) -> Optional[str]:
    """Save video bytes to a file and return the path."""
    logger = logging.getLogger(__name__)
    try:
        if custom_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"veo3_video_{timestamp}.mp4"
            custom_path = os.path.join(tempfile.gettempdir(), video_filename)
        async with aiofiles.open(custom_path, 'wb') as f:
            await f.write(video_data)
        logger.info(f"Video data saved successfully: {custom_path}")
        return custom_path
    except Exception as e:
        logger.error(f"Failed to save video data: {e}")
        return None

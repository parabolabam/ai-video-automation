#!/usr/bin/env python3
"""
Download Veo 3 generated video file given a Gemini client and file handle (Kie domain)
"""

import logging
import os
import tempfile
from datetime import datetime
from typing import Optional, Any
from features.downloader.download_video import download_video_to_path


async def download_veo3_video(gemini_client: Any, video_file: Any) -> Optional[str]:
    """Download Veo 3 generated video file to temp path and return it."""
    logger = logging.getLogger(__name__)
    try:
        output_dir = os.getenv("VIDEO_OUTPUT_DIR", tempfile.gettempdir())
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"veo3_video_{timestamp}.mp4"
        video_path = os.path.join(output_dir, video_filename)

        try:
            gemini_client.files.download(file=video_file)
            video_file.save(video_path)
            return video_path
        except Exception:
            pass

        if hasattr(video_file, 'uri') and isinstance(video_file.uri, str):
            # Fallback to URI download via shared downloader
            import aiohttp
            async with aiohttp.ClientSession() as session:
                return await download_video_to_path(session, video_file.uri, video_path)

        if hasattr(video_file, 'data'):
            try:
                with open(video_path, 'wb') as f:
                    f.write(video_file.data)
                return video_path
            except Exception:
                return None

        return None
    except Exception as e:
        logger.error(f"Failed to download Veo 3 video: {e}")
        return None

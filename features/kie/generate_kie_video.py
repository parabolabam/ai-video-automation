#!/usr/bin/env python3
"""
Generate a video via Kie (veo3_fast) and return the local file path
"""

import os
from typing import Optional
from features.kie.video_apis import VideoGenerationAPI


async def generate_kie_video(prompt: str, duration: int | None = None, quality: str | None = None) -> Optional[str]:
    """Generate a Kie video and return local path or None."""
    _duration = int(os.getenv('VIDEO_DURATION', duration or 8))
    _quality = (quality or os.getenv('VIDEO_QUALITY', 'fast')).lower()
    api = VideoGenerationAPI('kie')
    return await api.generate_video(prompt, _duration, _quality)

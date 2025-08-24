#!/usr/bin/env python3
"""
Create an Instagram Reel media container
"""

import os
from typing import Optional, Dict, Any
import httpx

from features.core.load_env import load_env

load_env()

async def create_reel_container(video_url: str, caption: str, ig_user_id = os.getenv("IG_USER_ID"), access_token = os.getenv("IG_ACCESS_TOKEN")) -> Optional[str]:
    """Create an IG Reel container and return its creation_id (container id) or None."""
    api_ver = os.getenv("IG_API_VERSION", "v23.0")
    endpoint = f"https://graph.facebook.com/{api_ver}/{ig_user_id}/media"
    payload: Dict[str, Any] = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": access_token,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(endpoint, data=payload)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("id")

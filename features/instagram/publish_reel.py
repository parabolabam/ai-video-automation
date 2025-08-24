#!/usr/bin/env python3
"""
Publish an Instagram Reel container
"""

import logging
import os
from typing import Optional
import httpx


async def publish_reel(ig_user_id: str, access_token: str, creation_id: str) -> Optional[str]:
    logger = logging.getLogger(__name__)
    """Publish a media container and return media id or None."""
    api_ver = os.getenv("IG_API_VERSION", "v19.0")
    endpoint = f"https://graph.facebook.com/{api_ver}/{ig_user_id}/media_publish"
    payload = {
        "creation_id": creation_id,
        "access_token": access_token,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(endpoint, data=payload)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("id")

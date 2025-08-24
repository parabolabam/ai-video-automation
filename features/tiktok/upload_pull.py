#!/usr/bin/env python3
"""
TikTok upload via PULL_FROM_URL (Content Posting API)
"""

import os
from typing import Optional, Dict, Any
import httpx
import logging


async def init_pull_upload(access_token: str, video_url: str, caption: str) -> Optional[Dict[str, Any]]:
    """Init a pull-from-URL upload. Returns dict with publish_id or None."""
    endpoint = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {
        "source": "PULL_FROM_URL",
        "post_info": {
            "caption": caption,
            "privacy_level": os.getenv("TIKTOK_PRIVACY_LEVEL", "PUBLIC_TO_EVERYONE"),
        },
        "video_url": video_url,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(endpoint, headers=headers, json=data)
        if r.status_code != 200:
            logging.getLogger(__name__).warning(
                "TikTok init (PULL_FROM_URL) failed: %s %s", r.status_code, r.text
            )
            return {"error": r.text, "status_code": r.status_code}
        return r.json()


async def fetch_publish_status(access_token: str, publish_id: str) -> Optional[Dict[str, Any]]:
    endpoint = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    data = {"publish_id": publish_id}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(endpoint, headers=headers, json=data)
        if r.status_code != 200:
            logging.getLogger(__name__).warning(
                "TikTok status fetch failed: %s %s", r.status_code, r.text
            )
            return {"error": r.text, "status_code": r.status_code}
        return r.json()

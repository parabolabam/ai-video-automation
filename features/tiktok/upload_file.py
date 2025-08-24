#!/usr/bin/env python3
"""
TikTok upload via FILE_UPLOAD (Content Posting API)
"""

import os
import httpx
import aiofiles
from typing import Optional, Dict, Any
import logging
logger = logging.getLogger(__name__)


async def init_file_upload(access_token: str, caption: str, video_size_bytes: int) -> Optional[Dict[str, Any]]:
    """Initialize a file upload; returns dict with upload_url and publish_id or None."""
    endpoint = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    # Single-chunk upload by default; adjust if you later implement chunked uploads
    chunk_size = video_size_bytes
    total_chunk_count = 1
    data: Dict[str, Any] = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size_bytes,
            "chunk_size": chunk_size,
            "total_chunk_count": total_chunk_count,
            "is_aigc": True,
        },
        "post_info": {
            "caption": caption,
            "privacy_level": os.getenv("TIKTOK_PRIVACY_LEVEL", "SELF_ONLY"),
        },
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(endpoint, headers=headers, json=data)
        if r.status_code != 200:
            logging.getLogger(__name__).warning(
                "TikTok init (FILE_UPLOAD) failed: %s %s", r.status_code, r.text
            )
            return {"error": r.text, "status_code": r.status_code}
        return r.json()


async def put_file_to_upload_url(upload_url: str, file_path: str) -> bool:
    """PUT the full file to the given upload URL."""
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with aiofiles.open(file_path, 'rb') as f:
                data = await f.read()
            size = len(data)
            r = await client.put(
                upload_url,
                content=data,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(size),
                    "Content-Range": f"bytes 0-{size-1}/{size}",
                },
            )
            logger.debug("TikTok PUT upload responded: %s %s", r.status_code, r.text)
            return 200 <= r.status_code < 300
    except Exception as e:
        logger.error("put_file_to_upload_url error: %s", e)
        return False

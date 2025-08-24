#!/usr/bin/env python3
"""
TikTok upload via PULL_FROM_URL using long-lived access token
"""

import os
import logging
from typing import Optional
from .upload_file import init_file_upload, put_file_to_upload_url
from .token import get_access_token_for_run
from .poll import wait_until_published


async def tiktok_upload(video: str, caption: str) -> Optional[str]:
    """Upload to TikTok.

    - If `video` starts with http(s), use PULL_FROM_URL
    - Else, use FILE_UPLOAD with the local file path
    Returns publish_id or None.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting TikTok upload")
    # Allow disabling via environment flag
    if os.getenv("TIKTOK_UPLOAD_DISABLED"):
        logger.info("TIKTOK_UPLOAD_DISABLED is set; skipping TikTok upload")
        return None
    access_token = await get_access_token_for_run()
    if not access_token:
        logger.info("TIKTOK_ACCESS_TOKEN missing; skipping TikTok upload")
        return None

    # Only support local file uploads
    if video.startswith("http://") or video.startswith("https://"):
        logger.warning("TikTok upload is restricted to local files; got URL")
        return None
    if not os.path.isfile(video):
        logger.warning(f"TikTok upload file not found: {video}")
        return None

    logger.info("TikTok mode=FILE_UPLOAD")
    try:
        init = await init_file_upload(access_token, caption, os.path.getsize(video))
        if init and isinstance(init, dict) and init.get("data", {}).get("upload_url"):
            ok = await put_file_to_upload_url(init["data"]["upload_url"], video)
            if not ok:
                logger.warning("TikTok file upload failed")
                return None
        else:
            logger.warning(f"TikTok init (FILE_UPLOAD) missing upload_url: {init}")
            return None
        if not init or not isinstance(init, dict) or "data" not in init or "publish_id" not in init["data"]:
            logger.warning(f"TikTok init failed: {init}")
            return None
        publish_id = init["data"]["publish_id"]
        logger.info(f"TikTok init OK, publish_id={publish_id}")
        # Poll for status
        interval = int(os.getenv("TIKTOK_POLL_INTERVAL", 15))
        timeout = int(os.getenv("TIKTOK_POLL_TIMEOUT", 600))
        status = await wait_until_published(access_token, publish_id, interval, timeout)
        if status and "data" in status:
            st = status["data"].get("status") or status["data"].get("status_code")
            if st in ("SEND_TO_USER_INBOX","PUBLISH_COMPLETE", "PUBLISHED", "READY", "SUCCESS"):
                return publish_id
        return None
    except Exception as e:
        logger.warning(f"TikTok upload encountered an error and was skipped: {e}")
        return None

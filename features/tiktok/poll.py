#!/usr/bin/env python3
"""
Polling utilities for TikTok publish status
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from .upload_pull import fetch_publish_status


async def wait_until_published(access_token: str, publish_id: str, interval: int = 15, timeout: int = 600) -> Optional[Dict[str, Any]]:
    """Poll TikTok publish status until success, failure, or timeout.

    Returns the last status dict on success/failure, or None on timeout.
    """
    logger = logging.getLogger(__name__)
    elapsed = 0
    while elapsed < timeout:
        status = await fetch_publish_status(access_token, publish_id)
        logger.info(status)
        if status:
            data = status.get("data", {}) if isinstance(status, dict) else {}
            error = status.get("error", {}) if isinstance(status, dict) else {}
            st = (data.get("status") or data.get("status_code") or "").upper()
            # Treat multiple success indicators as terminal
            success_statuses = {"SEND_TO_USER_INBOX","PUBLISH_COMPLETE", "PUBLISHED", "READY", "SUCCESS", "PUBLISH_SUCCESS"}
            has_public_id = bool(data.get("publicaly_available_post_id") or data.get("publicly_available_post_id"))
            is_ok = (error.get("code") == "ok")
            if st in success_statuses or has_public_id or is_ok:
                logger.info(f"TikTok publish ready: {publish_id}")
                return status
            if st in {"FAILED", "ERROR"} or error.get("code") in {"failed", "error"}:
                logger.warning(f"TikTok publish failed: {status}")
                return status
        await asyncio.sleep(interval)
        elapsed += interval
    logger.warning("TikTok publish timed out")
    return None



#!/usr/bin/env python3
"""
TikTok token helper: obtain an access token for this run (refresh if possible)
"""

import os
import logging
from typing import Optional
from .auth import refresh_access_token


async def get_access_token_for_run() -> Optional[str]:
    """Return a usable TikTok access token.

    If refresh token and client creds are present, attempt refresh; otherwise
    return the TIKTOK_ACCESS_TOKEN from environment.
    """
    logger = logging.getLogger(__name__)
    access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
    refresh_token = os.getenv("TIKTOK_REFRESH_TOKEN")
    client_key = os.getenv("TIKTOK_CLIENT_KEY")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET")

    if refresh_token and client_key and client_secret:
        try:
            res = await refresh_access_token(client_key, client_secret, refresh_token)
            if res and res.get("access_token"):
                logger.info("Refreshed TikTok access token for this run")
                return res["access_token"]
        except Exception as e:
            logger.warning(f"TikTok token refresh failed: {e}")
    return access_token



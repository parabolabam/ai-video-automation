#!/usr/bin/env python3
"""
Generic async video downloader
"""

import aiohttp
import os
from typing import Optional


async def download_video_to_path(session: aiohttp.ClientSession, url: str, dest_path: str) -> Optional[str]:
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        async with session.get(url) as response:
            if response.status != 200:
                return None
            with open(dest_path, 'wb') as f:
                async for chunk in response.content.iter_chunked(1024):
                    f.write(chunk)
        return dest_path
    except Exception:
        return None

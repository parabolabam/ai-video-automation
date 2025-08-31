#!/usr/bin/env python3
"""
Poll a Kie.ai Veo generation job until completion and download the video (simple)
"""

import aiohttp
import asyncio
import logging
import os
import tempfile
from datetime import datetime
from typing import Optional
from features.downloader.download_video import download_video_to_path


async def poll_kie_status(task_id: str, status_url: Optional[str] = None, timeout_seconds: int | None = None) -> Optional[str]:
    """Poll the Kie job until completed and download the resulting video.

    Returns path to the downloaded video, or None on failure/timeout.
    Requires KIE_API_KEY in environment.
    """
    logger = logging.getLogger(__name__)

    api_key = os.getenv("KIE_API_KEY")
    if not api_key:
        logger.error("KIE_API_KEY is not set")
        return None

    base_url = os.getenv("KIE_BASE_URL", "https://api.kie.ai/api/v1")
    status_url = status_url or f"{base_url}/veo/record-info?taskId={task_id}"

    if timeout_seconds is None:
        timeout_seconds = int(os.getenv("VEO_MAX_WAIT_TIME", 600))

    check_interval = 15
    elapsed_time = 0
    headers = {"Authorization": f"Bearer {api_key}"}

    async with aiohttp.ClientSession() as session:
        while elapsed_time < timeout_seconds:
            try:
                async with session.get(status_url, headers=headers) as response:
                    logger.info(
                        f"Kie poll: task_id={task_id} elapsed={elapsed_time}s status={response.status}"
                    )
                    if response.status == 200:
                        result = await response.json()
                        data = result["data"]
                        flag = str(data["successFlag"])  # "0", "1", "2", or "3"
                        logger.info(f"Kie poll: successFlag={flag}")
                        if flag == "1":
                            urls = data["response"]["resultUrls"]
                            if urls:
                                logger.info(
                                    f"Kie poll: result URL received ({len(urls)} urls). Downloading..."
                                )
                                return await _download_video(session, urls[0], task_id)
                            return None
                        if flag in {"2", "3"}:
                            logger.warning(
                                f"Kie poll: terminal flag={flag} without result. Aborting."
                            )
                            return None
                    # non-200 → fall through to sleep/retry
            except Exception as e:
                # Any parsing/network error → retry until timeout
                logger.warning(
                    f"Kie poll: transient error while parsing/reading status; retrying..., {e}"
                )

            await asyncio.sleep(check_interval)
            elapsed_time += check_interval

        return None


async def poll_kie_status_for_url(
    task_id: str, status_url: Optional[str] = None, timeout_seconds: int | None = None
) -> Optional[str]:
    """
    Poll the Kie job until completed and return the resulting video URL (no download).

    Returns the first URL as a string, or None on failure/timeout.
    Requires KIE_API_KEY in environment.
    """
    logger = logging.getLogger(__name__)

    api_key = os.getenv("KIE_API_KEY")
    if not api_key:
        logger.error("KIE_API_KEY is not set")
        return None

    base_url = os.getenv("KIE_BASE_URL", "https://api.kie.ai/api/v1")
    status_url = status_url or f"{base_url}/veo/record-info?taskId={task_id}"

    if timeout_seconds is None:
        timeout_seconds = int(os.getenv("VEO_MAX_WAIT_TIME", 600))

    check_interval = 15
    elapsed_time = 0
    headers = {"Authorization": f"Bearer {api_key}"}

    async with aiohttp.ClientSession() as session:
        while elapsed_time < timeout_seconds:
            try:
                async with session.get(status_url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        data = result["data"]
                        flag = str(data["successFlag"])  # "0", "1", "2", or "3"
                        if flag == "1":
                            urls = data["response"]["resultUrls"]
                            if urls:
                                return urls[0]
                            return None
                        if flag in {"2", "3"}:
                            return None
                    # non-200 → fall through to sleep/retry
            except Exception:
                # Any parsing/network error → retry until timeout
                pass

            await asyncio.sleep(check_interval)
            elapsed_time += check_interval

        return None


async def _download_video(session: aiohttp.ClientSession, video_url: str, task_id: str) -> Optional[str]:
    output_dir = os.getenv("VIDEO_OUTPUT_DIR", tempfile.gettempdir())
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kie_video_{timestamp}_{task_id[:8]}.mp4"
    path = os.path.join(output_dir, filename)
    return await download_video_to_path(session, video_url, path)

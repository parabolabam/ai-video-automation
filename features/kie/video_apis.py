#!/usr/bin/env python3
"""
Kie.ai Veo3 client (fast model)
"""

import asyncio
import aiohttp
import logging
import os
import tempfile
import json
from typing import Optional, Dict, Any
from features.downloader.download_video import download_video_to_path
from datetime import datetime

logger = logging.getLogger(__name__)


class VideoGenerationAPI:
    def __init__(self, provider: str = "kie"):
        self.provider = "kie"
        self.api_key = os.getenv("KIE_API_KEY")
        if not self.api_key:
            raise ValueError("KIE_API_KEY not set")
        self.base_url = os.getenv("KIE_BASE_URL", "https://api.kie.ai/api/v1")

    async def generate_video(self, prompt: str, duration: int = 8, quality: str = "fast") -> Optional[str]:
        return await self._generate_kie(prompt, duration, quality)

    async def _generate_kie(self, prompt: str, duration: int, quality: str) -> Optional[str]:
        url = f"{self.base_url}/veo/generate"
        model = "veo3_fast"
        payload = {
            "prompt": f"Vertical 9:16 aspect ratio, {prompt}. High quality, engaging, 8 seconds.",
            "mode": "fast",
            "duration": duration,
            "aspectRatio": "9:16",
            "model": model
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        return await self._make_request_and_poll(url, payload, headers)

    async def _make_request_and_poll(self, url: str, payload: Dict, headers: Dict) -> Optional[str]:
        max_wait_time = int(os.getenv('VEO_MAX_WAIT_TIME', 600))
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    return None
                result = await response.json()
                job_id = result.get("data", {}).get("taskId")
                if not job_id:
                    return None
                return await self._poll_for_completion(session, job_id, headers, max_wait_time)

    async def _poll_for_completion(self, session: aiohttp.ClientSession, job_id: str, headers: Dict, max_wait_time: int) -> Optional[str]:
        status_url = f"{self.base_url}/veo/record-info?taskId={job_id}"
        check_interval = 15
        elapsed = 0
        while elapsed < max_wait_time:
            async with session.get(status_url, headers=headers) as resp:
                if resp.status == 200:
                    r = await resp.json()
                    d = r["data"]
                    if str(d["successFlag"]) == "1":
                        url = d["response"]["resultUrls"][0]
                        return await self._download_video(session, url, job_id)
                    if str(d["successFlag"]) in {"2", "3"}:
                        return None
            await asyncio.sleep(check_interval)
            elapsed += check_interval
        return None

    async def _download_video(self, session: aiohttp.ClientSession, video_url: str, job_id: str) -> Optional[str]:
        output_dir = os.getenv("VIDEO_OUTPUT_DIR", tempfile.gettempdir())
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(output_dir, f"kie_video_{timestamp}_{job_id[:8]}.mp4")
        return await download_video_to_path(session, video_url, path)

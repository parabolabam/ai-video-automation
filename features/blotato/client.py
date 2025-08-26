#!/usr/bin/env python3
"""
Thin async client for Blotato API.

Endpoints used:
- POST /v2/media           -> upload media (via URL or multipart file)
- POST /v2/posts           -> publish or schedule posts

Docs: https://help.blotato.com/api/api-reference
"""

import asyncio
import json
import mimetypes
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp


BLOTATO_BASE_URL = "https://backend.blotato.com"


class BlotatoError(Exception):
    pass


@dataclass
class BlotatoPostTarget:
    targetType: str  # e.g., "instagram", "tiktok", "youtube"
    pageId: Optional[str] = None  # optional depending on platform


class BlotatoClient:
    def __init__(self, api_key: str, base_url: str = BLOTATO_BASE_URL) -> None:
        if not api_key:
            raise ValueError("BLOTATO_API_KEY is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        return {
            "blotato-api-key": self.api_key,
            "Accept": "application/json",
        }

    async def _raise_for_status(self, resp: aiohttp.ClientResponse) -> None:
        if 200 <= resp.status < 300:
            return
        try:
            payload = await resp.json()
        except Exception as e:
            payload = f"<no body: {e}>"
        raise BlotatoError(f"HTTP {resp.status} from {resp.url}: {payload}")

    def _should_retry(self, status_code: int) -> bool:
        # Retry on common transient statuses
        return status_code in (429, 500, 502, 503, 504)

    async def upload_media(
        self,
        *,
        url: Optional[str] = None,
        file_path: Optional[str] = None,
        max_retries: int = 3,
        retry_backoff_base: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Upload a media asset to Blotato.

        Preferred usage: provide a public URL via `url`.
        If you only have a local file, pass `file_path`. We'll attempt multipart upload.
        Returns response JSON (should include hosted URL/id consumable by posts).
        """
        if not url and not file_path:
            raise ValueError("Either url or file_path must be provided")

        media_endpoint = f"{self.base_url}/v2/media"
        async with aiohttp.ClientSession(
            headers=self._headers(), timeout=aiohttp.ClientTimeout(total=60)
        ) as session:
            attempt = 0
            while True:
                attempt += 1
                try:
                    if url:
                        async with session.post(
                            media_endpoint, json={"url": url}
                        ) as resp:
                            if (
                                self._should_retry(resp.status)
                                and attempt <= max_retries
                            ):
                                await asyncio.sleep(
                                    retry_backoff_base * (2 ** (attempt - 1))
                                )
                                continue
                            await self._raise_for_status(resp)
                            return await resp.json()

                    # Multipart upload for local files
                    assert file_path is not None
                    filename = os.path.basename(file_path)
                    guessed_type, _ = mimetypes.guess_type(filename)
                    content_type = guessed_type or "application/octet-stream"

                    form = aiohttp.FormData()
                    form.add_field(
                        name="file",
                        value=open(file_path, "rb"),
                        filename=filename,
                        content_type=content_type,
                    )
                    # Ensure we do not send a JSON Content-Type for multipart
                    async with session.post(
                        media_endpoint,
                        data=form,
                        headers={
                            k: v
                            for k, v in self._headers().items()
                            if k.lower() != "content-type"
                        },
                    ) as resp:
                        if self._should_retry(resp.status) and attempt <= max_retries:
                            await asyncio.sleep(
                                retry_backoff_base * (2 ** (attempt - 1))
                            )
                            continue
                        await self._raise_for_status(resp)
                        return await resp.json()
                except BlotatoError:
                    if attempt <= max_retries:
                        await asyncio.sleep(retry_backoff_base * (2 ** (attempt - 1)))
                        continue
                    raise

    async def publish_post(
        self,
        *,
        account_id: str,
        platform: str,
        text: str,
        media_urls: Optional[List[str]] = None,
        target: Optional[BlotatoPostTarget] = None,
        scheduled_time_iso: Optional[str] = None,
        max_retries: int = 3,
        retry_backoff_base: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Publish or schedule a post.

        - platform examples: "instagram", "tiktok", "youtube", "bluesky", etc.
        - target: additional targeting info; minimally includes targetType.
        - scheduled_time_iso: when provided, schedules in ISO 8601 UTC.
        """
        post_endpoint = f"{self.base_url}/v2/posts"
        content: Dict[str, Any] = {
            "text": text,
            "platform": platform,
        }
        if media_urls:
            content["mediaUrls"] = media_urls

        target_payload: Dict[str, Any] = {"targetType": platform}
        if target:
            target_payload["targetType"] = target.targetType
            if target.pageId:
                target_payload["pageId"] = target.pageId

        # Provider-specific required fields
        if platform == "youtube":
            # Required by Blotato for YouTube
            yt_title = (
                os.getenv("BLOTATO_YOUTUBE_TITLE")
                or content.get("text")
                or "AI Generated"
            )
            yt_privacy = (
                os.getenv("BLOTATO_YOUTUBE_PRIVACY_STATUS") or "public"
            ).lower()
            yt_notify_str = (
                (os.getenv("BLOTATO_YOUTUBE_NOTIFY_SUBSCRIBERS") or "false")
                .strip()
                .lower()
            )
            yt_notify = yt_notify_str in {"1", "true", "yes", "y"}

            target_payload["title"] = yt_title[:100]
            target_payload["privacyStatus"] = yt_privacy
            target_payload["shouldNotifySubscribers"] = yt_notify

        payload: Dict[str, Any] = {
            "post": {
                "accountId": account_id,
                "content": content,
                "target": target_payload,
            }
        }
        if scheduled_time_iso:
            payload["scheduledTime"] = scheduled_time_iso

        async with aiohttp.ClientSession(
            headers=self._headers(),
            timeout=aiohttp.ClientTimeout(total=60),
        ) as session:
            attempt = 0
            while True:
                attempt += 1
                async with session.post(
                    post_endpoint,
                    headers={**self._headers(), "Content-Type": "application/json"},
                    json=payload,
                ) as resp:
                    if self._should_retry(resp.status) and attempt <= max_retries:
                        await asyncio.sleep(retry_backoff_base * (2 ** (attempt - 1)))
                        continue
                    await self._raise_for_status(resp)
                    return await resp.json()

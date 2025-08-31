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
import random


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

    async def _sleep_backoff(self, attempt: int, backoff_base: float) -> None:
        base = backoff_base * (2 ** (attempt - 1))
        await asyncio.sleep(base + random.uniform(0, 0.5))

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
        eff_max_retries = int(os.getenv("BLOTATO_MAX_RETRIES", str(max_retries)))
        eff_backoff = float(
            os.getenv("BLOTATO_RETRY_BACKOFF_BASE", str(retry_backoff_base))
        )
        eff_timeout = float(os.getenv("BLOTATO_TIMEOUT_TOTAL", "90"))

        async with aiohttp.ClientSession(
            headers=self._headers(), timeout=aiohttp.ClientTimeout(total=eff_timeout)
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
                                and attempt <= eff_max_retries
                            ):
                                await self._sleep_backoff(attempt, eff_backoff)
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
                        if (
                            self._should_retry(resp.status)
                            and attempt <= eff_max_retries
                        ):
                            await self._sleep_backoff(attempt, eff_backoff)
                            continue
                        await self._raise_for_status(resp)
                        return await resp.json()
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt <= eff_max_retries:
                        await self._sleep_backoff(attempt, eff_backoff)
                        continue
                    raise BlotatoError(f"Network error during upload_media: {e}")
                except BlotatoError:
                    if attempt <= eff_max_retries:
                        await self._sleep_backoff(attempt, eff_backoff)
                        continue
                    raise

    async def publish_post(
        self,
        *,
        account_id: Optional[str] = None,
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

        post_body: Dict[str, Any] = {
            "content": content,
            "target": target_payload,
        }
        if account_id:
            post_body["accountId"] = account_id

        payload: Dict[str, Any] = {"post": post_body}
        if scheduled_time_iso:
            payload["scheduledTime"] = scheduled_time_iso

        eff_max_retries = int(os.getenv("BLOTATO_MAX_RETRIES", str(max_retries)))
        eff_backoff = float(
            os.getenv("BLOTATO_RETRY_BACKOFF_BASE", str(retry_backoff_base))
        )
        eff_timeout = float(os.getenv("BLOTATO_TIMEOUT_TOTAL", "90"))

        async with aiohttp.ClientSession(
            headers=self._headers(),
            timeout=aiohttp.ClientTimeout(total=eff_timeout),
        ) as session:
            attempt = 0
            while True:
                attempt += 1
                try:
                    async with session.post(
                        post_endpoint,
                        headers={**self._headers(), "Content-Type": "application/json"},
                        json=payload,
                    ) as resp:
                        if (
                            self._should_retry(resp.status)
                            and attempt <= eff_max_retries
                        ):
                            await self._sleep_backoff(attempt, eff_backoff)
                            continue
                        await self._raise_for_status(resp)
                        return await resp.json()
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt <= eff_max_retries:
                        await self._sleep_backoff(attempt, eff_backoff)
                        continue
                    raise BlotatoError(f"Network error during publish_post: {e}")

    async def publish_with_target_fields(
        self,
        *,
        account_id: Optional[str],
        platform: str,
        text: str,
        media_urls: List[str],
        target_fields: Dict[str, Any],
        scheduled_time_iso: Optional[str] = None,
        max_retries: int = 3,
        retry_backoff_base: float = 1.0,
    ) -> Dict[str, Any]:
        """Generic publisher that accepts provider-specific target fields.

        This method assembles the full payload and performs the HTTP request.
        """
        post_endpoint = f"{self.base_url}/v2/posts"
        content: Dict[str, Any] = {
            "text": text,
            "platform": platform,
            "mediaUrls": media_urls,
        }
        target_payload: Dict[str, Any] = {"targetType": platform}
        # Merge provided target fields (including optional pageId, privacy, etc.)
        for k, v in target_fields.items():
            if v is not None:
                target_payload[k] = v

        post_body: Dict[str, Any] = {
            "content": content,
            "target": target_payload,
        }
        if account_id:
            post_body["accountId"] = account_id
        payload: Dict[str, Any] = {"post": post_body}
        if scheduled_time_iso:
            payload["scheduledTime"] = scheduled_time_iso

        eff_max_retries = int(os.getenv("BLOTATO_MAX_RETRIES", str(max_retries)))
        eff_backoff = float(
            os.getenv("BLOTATO_RETRY_BACKOFF_BASE", str(retry_backoff_base))
        )
        eff_timeout = float(os.getenv("BLOTATO_TIMEOUT_TOTAL", "90"))

        async with aiohttp.ClientSession(
            headers=self._headers(),
            timeout=aiohttp.ClientTimeout(total=eff_timeout),
        ) as session:
            attempt = 0
            while True:
                attempt += 1
                try:
                    async with session.post(
                        post_endpoint,
                        headers={**self._headers(), "Content-Type": "application/json"},
                        json=payload,
                    ) as resp:
                        if (
                            self._should_retry(resp.status)
                            and attempt <= eff_max_retries
                        ):
                            await self._sleep_backoff(attempt, eff_backoff)
                            continue
                        await self._raise_for_status(resp)
                        return await resp.json()
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt <= eff_max_retries:
                        await self._sleep_backoff(attempt, eff_backoff)
                        continue
                    raise BlotatoError(
                        f"Network error during publish_with_target_fields: {e}"
                    )

    async def publish_youtube_post(
        self,
        *,
        account_id: Optional[str],
        text: str,
        media_urls: List[str],
        page_id: Optional[str] = None,
        scheduled_time_iso: Optional[str] = None,
        max_retries: int = 3,
        retry_backoff_base: float = 1.0,
    ) -> Dict[str, Any]:
        """Publish a YouTube post with platform-specific target fields prepared.

        Expects media_urls to contain a single Blotato-hosted URL.
        """
        yt_title = os.getenv("BLOTATO_YOUTUBE_TITLE") or text or "AI Generated"
        yt_privacy = (os.getenv("BLOTATO_YOUTUBE_PRIVACY_STATUS") or "public").lower()
        yt_notify_str = (
            (os.getenv("BLOTATO_YOUTUBE_NOTIFY_SUBSCRIBERS") or "false").strip().lower()
        )
        yt_notify = yt_notify_str in {"1", "true", "yes", "y"}
        target_fields = {
            "pageId": page_id,
            "title": yt_title[:100],
            "privacyStatus": yt_privacy,
            "shouldNotifySubscribers": yt_notify,
        }
        return await self.publish_with_target_fields(
            account_id=account_id,
            platform="youtube",
            text=text,
            media_urls=media_urls,
            target_fields=target_fields,
            scheduled_time_iso=scheduled_time_iso,
            max_retries=max_retries,
            retry_backoff_base=retry_backoff_base,
        )

    async def publish_instagram_post(
        self,
        *,
        account_id: Optional[str],
        text: str,
        media_urls: List[str],
        page_id: Optional[str] = None,
        scheduled_time_iso: Optional[str] = None,
        max_retries: int = 3,
        retry_backoff_base: float = 1.0,
    ) -> Dict[str, Any]:
        """Publish an Instagram post. No extra target fields are required beyond targetType/pageId."""
        return await self.publish_with_target_fields(
            account_id=account_id,
            platform="instagram",
            text=text,
            media_urls=media_urls,
            target_fields={"pageId": page_id} if page_id else {},
            scheduled_time_iso=scheduled_time_iso,
            max_retries=max_retries,
            retry_backoff_base=retry_backoff_base,
        )

    async def publish_tiktok_post(
        self,
        *,
        account_id: Optional[str],
        text: str,
        media_urls: List[str],
        page_id: Optional[str] = None,
        scheduled_time_iso: Optional[str] = None,
        max_retries: int = 3,
        retry_backoff_base: float = 1.0,
    ) -> Dict[str, Any]:
        """Publish a TikTok post with TikTok-specific target fields handled by publish_post."""
        raw_privacy = (
            (os.getenv("BLOTATO_TIKTOK_PRIVACY_LEVEL") or "public").strip().lower()
        )
        privacy_map = {
            "public": "PUBLIC_TO_EVERYONE",
            "everyone": "PUBLIC_TO_EVERYONE",
            "self_only": "SELF_ONLY",
            "private": "SELF_ONLY",
            "friends": "MUTUAL_FOLLOW_FRIENDS",
            "mutual_friends": "MUTUAL_FOLLOW_FRIENDS",
            "followers": "FOLLOWER_OF_CREATOR",
            "follower_of_creator": "FOLLOWER_OF_CREATOR",
        }
        tk_privacy = privacy_map.get(raw_privacy, "PUBLIC_TO_EVERYONE")

        def _b(name: str, default: str) -> bool:
            v = (os.getenv(name) or default).strip().lower()
            return v in {"1", "true", "yes", "y"}

        target_fields = {
            "pageId": page_id,
            "privacyLevel": tk_privacy,
            "disabledComments": _b("BLOTATO_TIKTOK_DISABLED_COMMENTS", "false"),
            "disabledDuet": _b("BLOTATO_TIKTOK_DISABLED_DUET", "false"),
            "disabledStitch": _b("BLOTATO_TIKTOK_DISABLED_STITCH", "false"),
            "isBrandedContent": _b("BLOTATO_TIKTOK_BRANDED_CONTENT", "false"),
            "isYourBrand": _b("BLOTATO_TIKTOK_IS_YOUR_BRAND", "false"),
            "isAiGenerated": True,
        }
        return await self.publish_with_target_fields(
            account_id=account_id,
            platform="tiktok",
            text=text,
            media_urls=media_urls,
            target_fields=target_fields,
            scheduled_time_iso=scheduled_time_iso,
            max_retries=max_retries,
            retry_backoff_base=retry_backoff_base,
        )

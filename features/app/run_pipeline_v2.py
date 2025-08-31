#!/usr/bin/env python3
"""
Run the v2 pipeline: generate prompt, create video (Kie), then publish via Blotato.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from features.openai.gen_prompt import generate_creative_prompt
from features.openai.gen_prompt import generate_trending_hashtags
from features.kie.video_apis import VideoGenerationAPI
from features.kie.poll_with_task_id import poll_with_task_id
from features.kie.poll_kie_status import poll_kie_status_for_url
from features.blotato.client import BlotatoClient, BlotatoPostTarget


async def post_one(
    client: BlotatoClient,
    *,
    hosted_media_url: str,
    post_text: str,
    scheduled_time_iso: Optional[str],
    target_cfg: Dict[str, Any],
    posted_keys: Set[Tuple[str, str, str, str]],
    logger: logging.Logger,
) -> bool:
    """Publish to a single target using platform-specific client helpers.

    Returns True on success, False on failure. Ensures no duplicate post for the
    same (platform, pageId, media) tuple by checking posted_keys.
    """
    platform = str(target_cfg.get("platform", "")).lower()
    page_id = target_cfg.get("pageId")
    # Optional account IDs per platform if required by Blotato
    account_id = None
    if platform == "tiktok":
        account_id = os.getenv("TIKTOK_ACCOUNT_ID")
    elif platform == "youtube":
        account_id = os.getenv("BLOTATO_ACCOUNT_ID_YOUTUBE")
    elif platform == "instagram":
        account_id = os.getenv("BLOTATO_ACCOUNT_ID_INSTAGRAM")
    if not platform:
        logger.warning(f"Skipping target missing platform: {target_cfg}")
        return False
    # Dedup key includes platform, pageId (or empty), accountId (or empty), and hosted media URL
    dedup_key = (platform, str(page_id or ""), str(account_id or ""), hosted_media_url)
    if dedup_key in posted_keys:
        logger.info(
            f"Skipping duplicate post for {platform} (pageId={page_id}, accountId={account_id})"
        )
        return True
    try:
        if platform == "youtube":
            resp = await client.publish_youtube_post(
                account_id=account_id,
                text=post_text,
                media_urls=[hosted_media_url],
                page_id=page_id,
                scheduled_time_iso=scheduled_time_iso,
            )
        elif platform == "instagram":
            resp = await client.publish_instagram_post(
                account_id=account_id,
                text=post_text,
                media_urls=[hosted_media_url],
                page_id=page_id,
                scheduled_time_iso=scheduled_time_iso,
            )
        else:
            # Default to TikTok helper for unknown here if configured that way
            resp = await client.publish_tiktok_post(
                account_id=account_id,
                text=post_text,
                media_urls=[hosted_media_url],
                page_id=page_id,
                scheduled_time_iso=scheduled_time_iso,
            )
        posted_keys.add(dedup_key)
        logger.info(f"Published via Blotato to {platform}: {resp}")
        return True
    except Exception as e:
        logger.error(f"Blotato post failed for {platform}: {e}")
        raise RuntimeError(f"Publish failed for {platform}") from e


async def build_hashtags(
    openai_client: Any,
    src: Optional[str],
    platform: Optional[str] = None,
) -> str:
    """Generate discovery-oriented hashtags using OpenAI (with override and fallback).

    - If BLOTATO_HASHTAGS is set (comma-separated), use that.
    - Else use OpenAI to generate platform-appropriate tags.
    - Fallback to simple extraction if OpenAI fails.
    """
    override = os.getenv("BLOTATO_HASHTAGS")
    if override:
        tags = [f"#{t.strip().lstrip('#')}" for t in override.split(",") if t.strip()]
        return " ".join(dict.fromkeys(tags))[:200]
    if not src:
        return "#ai #viral #shorts"
    try:
        plat = (platform or os.getenv("DEFAULT_PLATFORM") or "tiktok").lower()
        tags = await generate_trending_hashtags(openai_client, plat, src)
        tags = [f"#{t}" for t in tags]
        return " ".join(dict.fromkeys(tags))[:200]
    except Exception:
        words = [
            w.strip().lower() for w in src.replace("\n", " ").split(" ") if w.strip()
        ]
        words = ["".join(ch for ch in w if ch.isalnum()) for w in words]
        words = [w for w in words if len(w) >= 4][:5]
        defaults = ["ai", "viral", "shorts"]
        uniq: list[str] = []
        for w in words + defaults:
            tag = f"#{w}"
            if w and tag not in uniq:
                uniq.append(tag)
        return " ".join(uniq)[:200]


async def run_pipeline_v2(openai_client: Any) -> bool:
    """Run the pipeline and publish to social via Blotato."""
    logger = logging.getLogger(__name__)
    try:
        logger.info("Starting v2 pipeline (Blotato)...")

        task_id = os.getenv("TASK_ID")
        prompt = None
        video_path = None
        if task_id:
            logger.info(
                f"TASK_ID detected: {task_id}. Skipping generation; polling Kie for completion."
            )
            video_path = await poll_with_task_id(task_id)
            if not video_path:
                logger.error("Polling did not produce a downloadable video.")
                return False
        else:
            prompt = await generate_creative_prompt(openai_client)
            duration = int(os.getenv("VIDEO_DURATION", 8))
            quality = os.getenv("VIDEO_QUALITY", "fast").lower()
            video_path = await VideoGenerationAPI("kie").generate_video(prompt, duration, quality)
            if not video_path:
                logger.error("Video generation failed in v2 pipeline.")
                return False

        blotato_api_key = os.getenv("BLOTATO_API_KEY")
        if not blotato_api_key:
            logger.error("BLOTATO_API_KEY is not set. Aborting v2 pipeline.")
            return False
        client = BlotatoClient(api_key=blotato_api_key)

        # Resolve a direct URL if TASK_ID present (Kie URL); otherwise we have a local file path
        media_url = None
        if task_id:
            media_url = await poll_kie_status_for_url(task_id)

        # ALWAYS upload to Blotato from public URL; do not use multipart file uploads
        hosted_media_url: str | None = None
        try:
            uploaded = None
            if media_url:
                logger.info(f"Uploading to Blotato via URL: {media_url}")
                uploaded = await client.upload_media(url=media_url)
            else:
                logger.error(
                    "No public media URL available from Kie. Provide TASK_ID so we can poll the URL."
                )
                return False
            logger.info(f"Uploaded media to Blotato: {uploaded}")
            if isinstance(uploaded, dict):
                hosted_media_url = (
                    uploaded.get("url")
                    or uploaded.get("mediaUrl")
                    or uploaded.get("data", {}).get("url")
                )
            if not hosted_media_url:
                logger.error(
                    "Upload to Blotato did not return a media URL; aborting v2 pipeline."
                )
                return False
            logger.info("Blotato hosted media URL resolved")
        except Exception as e:
            logger.error(f"Failed to upload media to Blotato: {e}")
            return False

        # Multi-platform support: BLOTATO_TARGETS takes precedence if provided.
        # Example:
        # BLOTATO_TARGETS='[{"accountId":"acc_1","platform":"tiktok"},{"accountId":"acc_2","platform":"instagram","pageId":"..."}]'
        # Prefer explicit post text if provided, else derive from prompt (if any), else fallback
        explicit_text = os.getenv("BLOTATO_POST_TEXT")
        base_text = explicit_text or (
            f"{prompt[:180]}" if isinstance(prompt, str) else "AI Generated"
        )

        hashtags = await build_hashtags(
            openai_client,
            prompt if isinstance(prompt, str) else base_text,
        )
        post_text = f"{base_text}\n\n{hashtags}".strip()
        scheduled_time_iso = os.getenv("BLOTATO_SCHEDULED_TIME")  # optional ISO8601

        targets_raw = os.getenv("BLOTATO_TARGETS") or ""
        tasks: List[Any] = []
        if not targets_raw:
            raise ValueError("BLOTATO_TARGETS is not set")

        # Require JSON array form only
        targets_list_any = json.loads(targets_raw)
        if not isinstance(targets_list_any, list):
            logger.error("BLOTATO_TARGETS must be a JSON array of targets")
            return False
        targets_list: List[Dict[str, Any]] = targets_list_any  # type: ignore

        # Deduplicate targets to avoid double publishes (by platform + pageId)
        deduped: List[Dict[str, Any]] = []
        seen_keys = set()
        for t in targets_list:
            key = (str(t.get("platform", "")).lower(), str(t.get("pageId") or ""))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduped.append(t)
        targets_list = deduped

        # In-run dedup to prevent double publishes (same platform/page/media)
        posted_keys: set[tuple[str, str, str, str]] = set()

        for t in targets_list:
            tasks.append(
                post_one(
                    client,
                    hosted_media_url=hosted_media_url,
                    post_text=post_text,
                    scheduled_time_iso=scheduled_time_iso,
                    target_cfg=t,
                    posted_keys=posted_keys,
                    logger=logger,
                )
            )

        if tasks:
            results = await asyncio.gather(*tasks)
            if not all(results):
                logger.error("One or more platform posts failed")
                return False

        try:
            os.remove(video_path)
            logger.info(f"Removed local video file: {video_path}")
        except Exception as e:
            logger.warning(f"Failed to remove local video file: {e}")

        return True
    except Exception as e:
        logger.error(f"v2 pipeline failed: {e}")
        return False

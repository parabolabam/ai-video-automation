#!/usr/bin/env python3
"""
Run the v2 pipeline: generate prompt, create video (Kie), then publish via Blotato.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List

from features.openai.gen_prompt import generate_creative_prompt
from features.kie.video_apis import VideoGenerationAPI
from features.kie.poll_with_task_id import poll_with_task_id
from features.kie.poll_kie_status import poll_kie_status_for_url
from features.blotato.client import BlotatoClient, BlotatoPostTarget


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

        # ALWAYS upload to Blotato once and reuse hosted URL for all platforms
        hosted_media_url: str | None = None
        try:
            uploaded = None
            if media_url:
                uploaded = await client.upload_media(url=media_url)
            elif isinstance(video_path, str):
                uploaded = await client.upload_media(file_path=video_path)
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
        post_text = explicit_text or (f"{prompt[:180]}" if isinstance(prompt, str) else "AI Generated")
        scheduled_time_iso = os.getenv("BLOTATO_SCHEDULED_TIME")  # optional ISO8601

        targets_raw = os.getenv("BLOTATO_TARGETS")
        tasks: List[Any] = []
        if targets_raw:
            try:
                # Primary: JSON array form
                targets_list: List[Dict[str, Any]] = json.loads(targets_raw)
            except Exception:
                # Fallback: comma-separated platforms (use shared BLOTATO_ACCOUNT_ID / per-platform ACCOUNT envs if provided)
                platforms = [p.strip().lower() for p in targets_raw.split(",") if p.strip()]
                if not platforms:
                    logger.error("BLOTATO_TARGETS provided but empty after parsing.")
                    return False

                targets_list = []
                for platform in platforms:
                    # Do not use or require any accountId env variables; rely on Blotato defaults
                    page_id = os.getenv(f"BLOTATO_PAGE_ID_{platform.upper()}") or os.getenv("BLOTATO_PAGE_ID")
                    targets_list.append({"platform": platform, "pageId": page_id})

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
            posted_keys: set[tuple[str, str, str]] = set()

            async def post_one(target_cfg: Dict[str, Any]) -> None:
                platform = str(target_cfg.get("platform", "")).lower()
                page_id = target_cfg.get("pageId")
                # Optional account IDs per platform if required by Blotato
                account_id = None
                if platform == "tiktok":
                    account_id = os.getenv("TIKTOK_ACCOUNT_ID")
                elif platform == "youtube":
                    account_id = os.getenv("YOUTUBE_ACCOUNT_ID")
                elif platform == "instagram":
                    account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
                if not platform:
                    logger.warning(f"Skipping target missing platform: {target_cfg}")
                    return
                # Dedup key includes platform, pageId (or empty), and hosted media URL
                dedup_key = (platform, str(page_id or ""), hosted_media_url)
                if dedup_key in posted_keys:
                    logger.info(
                        f"Skipping duplicate post for {platform} (pageId={page_id})"
                    )
                    return
                target = BlotatoPostTarget(targetType=platform, pageId=page_id)
                try:
                    resp = await client.publish_post(
                        account_id=account_id,
                        platform=platform,
                        text=post_text,
                        media_urls=[hosted_media_url],
                        target=target,
                    )
                    posted_keys.add(dedup_key)
                    logger.info(f"Published via Blotato to {platform}: {resp}")
                except Exception as e:
                    logger.error(f"Blotato post failed for {platform}: {e}")

            for t in targets_list:
                tasks.append(post_one(t))
        else:
            # Fallback to single target via envs
            target_platform = os.getenv("BLOTATO_PLATFORM", "tiktok").lower()
            target = BlotatoPostTarget(targetType=target_platform, pageId=os.getenv("BLOTATO_PAGE_ID"))

            async def post_single() -> None:
                # Optional account IDs per platform if required by Blotato
                if target_platform == "tiktok":
                    account_id = os.getenv("TIKTOK_ACCOUNT_ID")
                elif target_platform == "youtube":
                    account_id = os.getenv("YOUTUBE_ACCOUNT_ID")
                elif target_platform == "instagram":
                    account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
                else:
                    account_id = None
                resp = await client.publish_post(
                    account_id=account_id,
                    platform=target_platform,
                    text=post_text,
                    media_urls=[hosted_media_url],
                    target=target,
                    scheduled_time_iso=scheduled_time_iso,
                )
                logger.info(f"Published via Blotato: {resp}")

            tasks.append(post_single())

        if tasks:
            await asyncio.gather(*tasks)

        try:
            os.remove(video_path)
            logger.info(f"Removed local video file: {video_path}")
        except Exception as e:
            logger.warning(f"Failed to remove local video file: {e}")

        return True
    except Exception as e:
        logger.error(f"v2 pipeline failed: {e}")
        return False

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

        # Prefer a public media URL for Blotato if possible
        media_url = None
        if task_id:
            media_url = await poll_kie_status_for_url(task_id)

        if not media_url and isinstance(video_path, str):
            # No URL available; use multipart upload to Blotato
            media_resp = await client.upload_media(file_path=video_path)
            logger.info(f"Uploaded media to Blotato: {media_resp}")
            if isinstance(media_resp, dict):
                media_url = media_resp.get("url") or media_resp.get("mediaUrl") or media_resp.get("data", {}).get("url")

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
                    # Prefer platform-specific account var if set, else global
                    specific_key = f"BLOTATO_ACCOUNT_ID_{platform.upper()}"
                    account_id = os.getenv(specific_key) or os.getenv("BLOTATO_ACCOUNT_ID")
                    page_id = os.getenv(f"BLOTATO_PAGE_ID_{platform.upper()}") or os.getenv("BLOTATO_PAGE_ID")
                    if not account_id:
                        logger.warning(f"Skipping {platform}: missing {specific_key} and BLOTATO_ACCOUNT_ID")
                        continue
                    targets_list.append({"platform": platform, "accountId": account_id, "pageId": page_id})

            async def post_one(target_cfg: Dict[str, Any]) -> None:
                platform = str(target_cfg.get("platform", "")).lower()
                account_id = target_cfg.get("accountId")
                page_id = target_cfg.get("pageId")
                if not platform or not account_id:
                    logger.warning(f"Skipping target missing platform/accountId: {target_cfg}")
                    return
                target = BlotatoPostTarget(targetType=platform, pageId=page_id)
                try:
                    resp = await client.publish_post(
                        account_id=account_id,
                        platform=platform,
                        text=post_text,
                        media_urls=[media_url] if media_url else None,
                        target=target,
                    )
                    logger.info(f"Published via Blotato to {platform}: {resp}")
                except Exception as e:
                    logger.error(f"Blotato post failed for {platform}: {e}")

            for t in targets_list:
                tasks.append(post_one(t))
        else:
            # Fallback to single target via envs
            target_platform = os.getenv("BLOTATO_PLATFORM", "tiktok").lower()
            account_id = os.getenv("BLOTATO_ACCOUNT_ID")
            if not account_id:
                logger.error("BLOTATO_ACCOUNT_ID is not set. Aborting v2 pipeline.")
                return False
            target = BlotatoPostTarget(targetType=target_platform, pageId=os.getenv("BLOTATO_PAGE_ID"))

            async def post_single() -> None:
                resp = await client.publish_post(
                    account_id=account_id,
                    platform=target_platform,
                    text=post_text,
                    media_urls=[media_url] if media_url else None,
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



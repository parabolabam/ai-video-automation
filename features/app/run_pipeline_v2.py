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


async def _generate_multi_scene_video(
    scenes: list[str],
    duration: int,
    quality: str,
    logger: logging.Logger,
) -> str:
    """Generate multiple video clips in PARALLEL and stitch them together.
    
    Args:
        scenes: List of scene prompts
        duration: Duration per scene in seconds
        quality: Video quality setting
        logger: Logger instance
        
    Returns:
        Path to the stitched video
    """
    from features.video.stitcher import stitch_videos
    
    video_api = VideoGenerationAPI("kie")
    
    # NEW APPROACH: Use Kie's extend API for seamless video without splicing
    # 1. Generate first scene
    # 2. Extend with each subsequent scene
    
    logger.info(f"Generating {len(scenes)} scenes using Kie extend API...")
    
    clips: list[str] = []
    
    # Step 1: Generate the first scene
    logger.info("Scene 1: Generating initial video...")
    current_task_id = await video_api.request_kie_task_id(scenes[0], duration, quality)
    if not current_task_id:
        raise RuntimeError("Failed to generate first scene")
    
    # Wait for first scene to complete
    first_video = await poll_with_task_id(current_task_id)
    if not first_video:
        raise RuntimeError("Failed to download first scene")
    logger.info(f"Scene 1 complete: {current_task_id}")
    clips.append(first_video)
    
    # Step 2: Extend with each subsequent scene
    for i, scene_prompt in enumerate(scenes[1:], start=2):
        logger.info(f"Scene {i}/{len(scenes)}: Extending video...")
        
        # Use extend API to add new content (generates next segment)
        new_task_id = await video_api.extend_kie_video(current_task_id, scene_prompt)
        if not new_task_id:
            logger.error(f"Failed to extend scene {i}, stopping extension")
            break
        
        # Wait for extension to complete
        extended_video = await poll_with_task_id(new_task_id)
        if not extended_video:
            logger.error(f"Failed to download extended scene {i}")
            break
            
        clips.append(extended_video)
        current_task_id = new_task_id
        logger.info(f"Scene {i} complete: {new_task_id}")
    
    if len(clips) > 1:
        logger.info(f"Stitching {len(clips)} extended clips...")
        stitched_video = await stitch_videos(clips)
        
        # Clean up intermediate clips if stitching succeeded
        for clip in clips:
            try:
                if clip != stitched_video and os.path.exists(clip):
                    os.remove(clip)
            except Exception as e:
                logger.warning(f"Failed to remove intermediate clip {clip}: {e}")
                
        return stitched_video
        
    return clips[0]


async def run_pipeline_v2(openai_client: Any) -> bool:
    """Run the pipeline and publish to social via Blotato.
    
    If PRODUCTION_MODE is not 'true', only downloads the video without publishing.
    If ENABLE_VOICEOVER is 'true', generates voiceover and composes with video.
    """
    logger = logging.getLogger(__name__)
    try:
        # Check production mode - default to false (safe mode)
        production_mode = os.getenv("PRODUCTION_MODE", "false").lower() == "true"
        enable_voiceover = os.getenv("ENABLE_VOICEOVER", "true").lower() == "true"
        
        if production_mode:
            logger.info("Starting v2 pipeline (PRODUCTION MODE - will publish)...")
        else:
            logger.info("Starting v2 pipeline (DEV MODE - download only, no publishing)...")

        task_id = os.getenv("TASK_ID")
        prompt = None
        voiceover_script = None
        video_path = None
        scenes = None
        extended_mode = os.getenv("EXTENDED_MODE", "false").lower() == "true"
        
        if not task_id:
            # Generate prompt (and voiceover script if using agent pipeline)
            prompt_result = await generate_creative_prompt(openai_client)
            
            # Handle different return types
            if isinstance(prompt_result, dict):
                if "scenes" in prompt_result:
                    # Extended mode - multi-scene
                    scenes = prompt_result.get("scenes", [])
                    voiceover_script = prompt_result.get("voiceover_script", "")
                    prompt = scenes[0] if scenes else ""
                    logger.info(f"Extended mode: {len(scenes)} scenes, {prompt_result.get('total_duration', 0)}s")
                else:
                    # Single scene agent pipeline
                    prompt = prompt_result.get("prompt", "")
                    voiceover_script = prompt_result.get("voiceover_script", "")
            else:
                prompt = prompt_result
            
            # Generate video(s)
            duration = int(os.getenv("VIDEO_DURATION", 8))
            quality = os.getenv("VIDEO_QUALITY", "fast").lower()
            
            if scenes and len(scenes) > 1:
                # Extended mode: generate multiple clips and stitch
                logger.info(f"Generating {len(scenes)} video clips...")
                video_path = await _generate_multi_scene_video(
                    scenes, duration, quality, logger
                )
            else:
                # Single clip generation
                task_id = await VideoGenerationAPI("kie").request_kie_task_id(
                    prompt, duration, quality
                )
                if not task_id:
                    logger.error("Failed to obtain Kie taskId")
                    return False
                logger.info(f"Obtained Kie taskId: {task_id}")
                video_path = await poll_with_task_id(task_id)
        else:
            # Using existing task_id
            video_path = await poll_with_task_id(task_id)

        if not video_path:
            logger.error("Polling did not produce a downloadable video.")
            return False

        # Calculate total duration for subtitles
        base_duration = int(os.getenv("VIDEO_DURATION", 8))
        total_duration = base_duration * len(scenes) if scenes else base_duration

        # Generate voiceover and compose video if enabled
        final_video_path = video_path
        enable_subtitles = os.getenv("ENABLE_SUBTITLES", "true").lower() == "true"
        
        if enable_voiceover and voiceover_script:
            logger.info("Generating voiceover audio...")
            try:
                from features.audio.tts import generate_voiceover
                from features.video.composer import compose_video_with_audio
                
                # Generate TTS audio
                audio_path = await generate_voiceover(
                    voiceover_script,
                    openai_client,
                )
                logger.info(f"Voiceover generated: {audio_path}")
                
                # Compose video with audio
                final_video_path = await compose_video_with_audio(
                    video_path,
                    audio_path,
                )
                logger.info(f"Video composed with audio: {final_video_path}")
                
                # Clean up original video and audio files
                try:
                    os.remove(video_path)
                    os.remove(audio_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp files: {e}")
                    
            except Exception as e:
                logger.error(f"Voiceover generation failed: {e}")
                # Continue with silent video instead of failing
                logger.info("Continuing with silent video...")
                final_video_path = video_path

        # Burn subtitles if enabled
        if enable_subtitles and voiceover_script:
            logger.info("Burning subtitles into video...")
            try:
                from features.video.subtitles import burn_subtitles
                from features.video.composer import get_video_duration
                
                # Get ACTUAL video duration from the file
                actual_duration = await get_video_duration(final_video_path)
                logger.info(f"Actual video duration: {actual_duration}s")
                
                video_before_subs = final_video_path
                final_video_path = await burn_subtitles(
                    video_path=final_video_path,
                    script=voiceover_script,
                    total_duration=actual_duration,  # Use actual duration, not calculated
                    font_size=int(os.getenv("SUBTITLE_FONT_SIZE", "28")),
                    words_per_subtitle=int(os.getenv("SUBTITLE_WORDS_PER_LINE", "5")),
                )
                logger.info(f"Subtitles burned: {final_video_path}")
                
                # Clean up video without subtitles
                if final_video_path != video_before_subs:
                    try:
                        os.remove(video_before_subs)
                    except Exception as e:
                        logger.warning(f"Failed to clean up pre-subtitle video: {e}")
                        
            except Exception as e:
                logger.error(f"Subtitle burn failed: {e}")
                logger.info("Continuing without subtitles...")

        # In non-production mode, stop here after downloading
        if not production_mode:
            logger.info(f"DEV MODE: Video downloaded to {final_video_path}")
            if voiceover_script:
                logger.info(f"DEV MODE: Voiceover script: {voiceover_script}")
            logger.info("DEV MODE: Skipping publishing. Set PRODUCTION_MODE=true to publish.")
            return True

        # --- Production mode: continue with publishing ---
        blotato_api_key = os.getenv("BLOTATO_API_KEY")
        if not blotato_api_key:
            logger.error("BLOTATO_API_KEY is not set. Aborting v2 pipeline.")
            return False
        client = BlotatoClient(api_key=blotato_api_key)

        # Resolve a direct URL if TASK_ID present (Kie URL); otherwise we have a local file path
        media_url = None
        if task_id:
            media_url = await poll_kie_status_for_url(task_id)
        if not media_url:
            logger.error(
                "Failed to obtain Kie media URL. TASK_ID is required and must resolve to a public URL."
            )
            return False

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
        logger.info(f"BLOTATO_TARGETS raw (first 200 chars): {targets_raw[:200]}")
        try:
            targets_list_any = json.loads(targets_raw)
        except Exception as e:
            logger.error(
                f"Failed to parse BLOTATO_TARGETS as JSON: {e}; raw snippet={targets_raw[:200]}"
            )
            return False
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

        if video_path != final_video_path:
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
                    logger.info(f"Removed local raw video file: {video_path}")
            except Exception as e:
                logger.warning(f"Failed to remove local raw video file: {e}")

        return True
    except Exception as e:
        logger.error(f"v2 pipeline failed: {e}")
        return False

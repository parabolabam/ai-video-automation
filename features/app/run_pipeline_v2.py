#!/usr/bin/env python3
"""
Run the v2 pipeline: Orchestrator using SOLID Domain Services.
Now uses native YouTube publishing instead of Blotato.
"""

import logging
import os
from typing import Any

from features.content.service import ContentService
from features.video.service import VideoGenerationService
from features.audio.service import AudioService
from features.post_production.service import PostProductionService
from features.publishing.service import PublishingService


async def run_pipeline_v2(openai_client: Any) -> bool:
    """Run the pipeline using domain services."""
    logger = logging.getLogger(__name__)

    # 1. Configuration
    production_mode = os.getenv("PRODUCTION_MODE", "false").lower() == "true"
    enable_voiceover = os.getenv("ENABLE_VOICEOVER", "true").lower() == "true"
    task_id = os.getenv("TASK_ID")

    # User ID for publishing (required for production mode)
    pipeline_user_id = os.getenv("PIPELINE_USER_ID")

    if production_mode:
        logger.info("Starting v2 pipeline (PRODUCTION MODE - will publish)...")
        if not pipeline_user_id:
            logger.error("PIPELINE_USER_ID is required for production mode")
            return False
    else:
        logger.info("Starting v2 pipeline (DEV MODE - agents only)...")

    # 2. Initialize Services
    content_svc = ContentService(openai_client)
    video_svc = VideoGenerationService()
    audio_svc = AudioService(openai_client)
    post_svc = PostProductionService()

    # Publishing service - uses native YouTube API
    pub_svc = PublishingService(pipeline_user_id) if pipeline_user_id else None

    # 3. Execution Flow
    video_path = None
    current_task_id = None
    voiceover_script = None
    prompt = None
    content = None

    try:
        if task_id:
            # Reusing existing generation
            video_path, current_task_id = await video_svc.retrieve_video(task_id)
            # Note: When reusing task_id, we skip content/script generation as we don't store state yet
        else:
            # Generate fresh content & video
            content = await content_svc.generate_content()
            prompt = content.get("prompt")
            voiceover_script = content.get("voiceover_script")
            scenes = content.get("scenes")

            if not production_mode:
                logger.info("DEV MODE: Content generated. Skipping video generation and upload.")
                logger.info(f"Generated Content: {content}")
                return True

            video_path, current_task_id = await video_svc.generate_video(prompt, scenes)

        if not video_path:
            logger.error("Video generation/retrieval failed")
            return False

        # 4. Post-Production (Audio + Composition)
        audio_path = None
        if enable_voiceover and voiceover_script:
            try:
                audio_path = await audio_svc.generate_voiceover(voiceover_script)
            except Exception as e:
                logger.error(f"Audio generation failed (continuing silent): {e}")

        final_path = await post_svc.process_video(video_path, audio_path, voiceover_script)
        logger.info(f"Final video ready: {final_path}")

        if not production_mode:
            logger.info("DEV MODE: Skipping publishing.")
            return True

        # 5. Publishing (using native YouTube API)
        if not pub_svc:
            logger.error("Publishing service not initialized (missing PIPELINE_USER_ID)")
            return False

        # Check if user has connected accounts
        connected_platforms = await pub_svc.get_connected_platforms()
        if not connected_platforms:
            logger.error("No connected accounts found. Please connect YouTube account first.")
            return False

        logger.info(f"Publishing to connected platforms: {connected_platforms}")

        sources = content.get("sources", []) if content else []

        if sources:
            # User request: "include only sources in video description" but WITH hashtags
            # Generate relevant hashtags based on the prompt (context)
            hashtags = await content_svc.generate_search_tags(prompt or "science facts")

            post_text = "Sources:\n"
            for src in sources:
                post_text += f"{src}\n"

            post_text += f"\n{hashtags}"
        else:
            # Fallback to generated metadata if no sources
            post_text = await content_svc.generate_metadata(prompt or "AI Video")

        # Publish to YouTube (and other connected platforms)
        results = await pub_svc.publish_video(
            file_path=final_path,
            title=prompt or "AI Generated Video",
            description=post_text,
            platforms=["youtube"],  # Only YouTube for Phase 1
        )

        # Check results
        youtube_result = results.get("youtube", {})
        if youtube_result.get("success"):
            logger.info(f"Published to YouTube: {youtube_result.get('url')}")
            return True
        else:
            logger.error(f"YouTube publishing failed: {youtube_result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return False

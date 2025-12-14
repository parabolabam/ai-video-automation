#!/usr/bin/env python3
"""
Run the v2 pipeline: Orchestrator using SOLID Domain Services.
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
    
    if production_mode:
        logger.info("Starting v2 pipeline (PRODUCTION MODE - will publish)...")
    else:
        logger.info("Starting v2 pipeline (DEV MODE - download only)...")

    # 2. Initialize Services
    content_svc = ContentService(openai_client)
    video_svc = VideoGenerationService()
    audio_svc = AudioService(openai_client)
    post_svc = PostProductionService()
    
    blotato_api_key = os.getenv("BLOTATO_API_KEY", "")
    pub_svc = PublishingService(blotato_api_key)

    # 3. Execution Flow
    video_path = None
    current_task_id = None
    voiceover_script = None
    prompt = None
    
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

        # 5. Publishing
        if not blotato_api_key:
            logger.error("BLOTATO_API_KEY missing, cannot publish")
            return False
            
        post_text = await content_svc.generate_metadata(prompt or "AI Video")
        
        # Append sources to description if available
        sources = content.get("sources", []) if content else []
        if sources:
            post_text += "\n\nSources / Fact Check:\n"
            for src in sources:
                post_text += f"- {src}\n"
        
        published = await pub_svc.publish_video(
            task_id=current_task_id,
            file_path=final_path,
            post_text=post_text,
            scheduled_time_iso=os.getenv("BLOTATO_SCHEDULED_TIME")
        )
        return published

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return False

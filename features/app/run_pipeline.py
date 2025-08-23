#!/usr/bin/env python3
"""
Run the complete automation pipeline
"""

import logging
import os
from typing import Any
from features.openai.gen_prompt import generate_creative_prompt
from features.kie.video_apis import VideoGenerationAPI
from features.youtube.upload_to_youtube import upload_to_youtube
from features.util.create_manual_video_instructions import create_manual_video_instructions
from features.util.create_demo_placeholder import create_demo_placeholder


async def run_pipeline(openai_client: Any, youtube_service: Any) -> bool:
    """Run the AI video automation pipeline end-to-end."""
    logger = logging.getLogger(__name__)
    try:
        logger.info("Starting video automation pipeline...")
        prompt = await generate_creative_prompt(openai_client)
        # Directly use Kie API
        duration = int(os.getenv('VIDEO_DURATION', 8))
        quality = os.getenv('VIDEO_QUALITY', 'fast').lower()
        video_path = await VideoGenerationAPI('kie').generate_video(prompt, duration, quality)
        if not video_path:
            logger.warning("Video generation failed with all methods.")
            await create_manual_video_instructions(prompt)
            await create_demo_placeholder(prompt)
            return False
        title = f"AI Generated: {prompt[:50]}..."
        description = f"Created with AI: {prompt}"
        video_url = upload_to_youtube(youtube_service, video_path, title, description)
        if video_url:
            logger.info(f"Pipeline completed successfully! Video: {video_url}")
            try:
                os.remove(video_path)
                logger.info(f"Removed local video file: {video_path}")
            except Exception as e:
                logger.warning(f"Failed to remove local video file: {e}")
            return True
        logger.error("Pipeline failed at YouTube upload step")
        return False
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return False

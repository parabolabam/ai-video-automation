#!/usr/bin/env python3
"""
AI Video Automation Orchestrator
"""

import asyncio
import logging
import os
from features.core.load_env import load_env
from features.core.configure_logging import configure_logging
from features.core.setup_apis import setup_apis
from features.tiktok.tiktok_upload import tiktok_upload
from features.kie.poll_with_task_id import poll_with_task_id
from features.kie.generate_kie_video import generate_kie_video
from features.youtube.upload_to_youtube import upload_to_youtube
from features.instagram.create_reel_container import create_reel_container
from features.instagram.publish_reel import publish_reel
from features.openai.gen_prompt import generate_creative_prompt

logger = logging.getLogger(__name__)

load_env()
configure_logging()


clients = setup_apis()
task_id = os.getenv("TASK_ID")


async def handle_existing_task_id(task_id):
    if task_id:
        video_path = await poll_with_task_id(task_id)
        logger.info(
            f"TASK_ID detected: {task_id}. Skipping generation; polling Kie for completion."
        )

        if not video_path:
            logger.error("Polling did not produce a downloadable video.")
            return

        await upload_to_youtube(
            clients["youtube_service"],
            video_path,
            f"AI Generated (Kie task {task_id[:8]})",
            f"Uploaded from Kie task {task_id}",
        )
        await tiktok_upload(video_path, "AI Generated")
        try:
            os.remove(video_path)
            logger.info(f"Removed local video file: {video_path}")
        except Exception as e:
            logger.warning(f"Failed to remove local video file: {e}")
        return


async def main() -> None:
    """Entry point: configure, setup APIs, and run the pipeline.

    If TASK_ID is provided in environment, skip prompt/generation and poll/download
    the Kie video directly, then upload to YouTube.
    """

    try:

        if task_id:
            await handle_existing_task_id(task_id)
            return

        prompt = await generate_creative_prompt(clients["openai_client"])
        video_path = await generate_kie_video(prompt)
        if not video_path:
            logger.error("Kie generation failed")
            return
        # Upload to YouTube
        await upload_to_youtube(
            clients["youtube_service"], video_path, "AI Generated", "Created with AI"
        )
        await tiktok_upload(video_path, "AI Generated")
        print("CALL")
        # Optional TikTok upload using a public URL (pull-based)

    except Exception as e:
        logger.error(f"Main execution failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())

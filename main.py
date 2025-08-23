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
from features.kie.poll_with_task_id import poll_with_task_id
from features.kie.generate_kie_video import generate_kie_video
from features.youtube.upload_to_youtube import upload_to_youtube
from features.openai.gen_prompt import generate_creative_prompt


async def main() -> None:
    """Entry point: configure, setup APIs, and run the pipeline.

    If TASK_ID is provided in environment, skip prompt/generation and poll/download
    the Kie video directly, then upload to YouTube.
    """
    load_env()
    configure_logging()
    logger = logging.getLogger(__name__)
    try:
        clients = setup_apis()

        task_id = os.getenv("TASK_ID")
        if task_id:
            video_path = await poll_with_task_id(task_id)
            logger.info(
                f"TASK_ID detected: {task_id}. Skipping generation; polling Kie for completion."
            )

            if not video_path:
                logger.error("Polling did not produce a downloadable video.")
                return
            title = f"AI Generated (Kie task {task_id[:8]})"
            description = f"Uploaded from Kie task {task_id}"
            upload_to_youtube(
                clients["youtube_service"], video_path, title, description
            )

            return

        prompt = await generate_creative_prompt(clients["openai_client"])
        video_path = await generate_kie_video(prompt)
        if not video_path:
            logger.error("Kie generation failed")
            return
        upload_to_youtube(
            clients["youtube_service"], video_path, f"AI Generated", f"Created with AI"
        )

    except Exception as e:
        logger.error(f"Main execution failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())

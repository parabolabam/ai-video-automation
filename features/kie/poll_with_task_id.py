import logging
from typing import Optional
from features.kie.poll_kie_status import poll_kie_status


logger = logging.getLogger(__name__)


async def poll_with_task_id(task_id: str) -> Optional[str]:
    """Poll Kie by task_id and return the downloaded video path (or None)."""
    logger.info(
        f"TASK_ID detected: {task_id}. Skipping generation; polling Kie for completion."
    )
    video_path = await poll_kie_status(task_id)
    if not video_path:
        logger.error("Polling did not produce a downloadable video.")
        return None
    return video_path
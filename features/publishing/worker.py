"""Background worker to process scheduled posts."""
import asyncio
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Optional

import httpx

from features.publishing.storage import (
    get_pending_posts_to_publish,
    get_account_by_id,
    update_post_status,
)
from features.publishing.service import PublishingService

logger = logging.getLogger(__name__)


async def download_video(url: str) -> Optional[str]:
    """Download video from URL to temp file. Returns path or None."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

            # Create temp file
            suffix = ".mp4"
            if "." in url.split("/")[-1]:
                suffix = "." + url.split(".")[-1]

            fd, path = tempfile.mkstemp(suffix=suffix)
            with os.fdopen(fd, "wb") as f:
                f.write(response.content)

            return path
    except Exception as e:
        logger.error(f"Failed to download video from {url}: {e}")
        return None


async def process_scheduled_posts():
    """Process all pending posts that are ready to publish."""
    posts = await get_pending_posts_to_publish()

    if not posts:
        return

    logger.info(f"Processing {len(posts)} scheduled posts")

    for post in posts:
        post_id = post["id"]
        user_id = post["user_id"]

        try:
            await update_post_status(post_id, "processing")

            # Download video if needed
            video_path = None
            video_url = post.get("video_url")

            if video_url:
                if video_url.startswith("/") or video_url.startswith("file://"):
                    # Local path
                    video_path = video_url.replace("file://", "")
                else:
                    # Remote URL - download it
                    video_path = await download_video(video_url)
                    if not video_path:
                        await update_post_status(post_id, "failed", "Failed to download video")
                        continue

            if not video_path:
                await update_post_status(post_id, "failed", "No video available")
                continue

            # Publish to all target accounts
            service = PublishingService(user_id)
            results = await service.publish_to_accounts(
                video_path=video_path,
                title=post["title"],
                description=post.get("description", ""),
                tags=post.get("tags", []),
                account_ids=post["target_account_ids"],
                scheduled_post_id=post_id,
            )

            # Clean up temp file if we downloaded it
            if video_url and not video_url.startswith("/") and not video_url.startswith("file://"):
                try:
                    os.unlink(video_path)
                except Exception:
                    pass

            # Check if all succeeded
            all_success = all(r.get("success") for r in results.values())
            any_success = any(r.get("success") for r in results.values())

            if all_success:
                await update_post_status(post_id, "completed")
                logger.info(f"Post {post_id} completed successfully")
            elif any_success:
                # Partial success
                errors = [f"{k}: {r.get('error')}" for k, r in results.items() if not r.get("success")]
                await update_post_status(post_id, "completed", f"Partial: {'; '.join(errors)}")
                logger.warning(f"Post {post_id} partially completed: {errors}")
            else:
                errors = [f"{k}: {r.get('error')}" for k, r in results.items()]
                await update_post_status(post_id, "failed", "; ".join(errors))
                logger.error(f"Post {post_id} failed: {errors}")

        except Exception as e:
            logger.error(f"Failed to process post {post_id}: {e}", exc_info=True)
            await update_post_status(post_id, "failed", str(e))


async def run_worker(interval_seconds: int = 60):
    """Run the worker loop."""
    logger.info(f"Starting scheduled post worker (interval: {interval_seconds}s)")

    while True:
        try:
            await process_scheduled_posts()
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)

        await asyncio.sleep(interval_seconds)


# For standalone execution
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())

"""Publishing service using native platform APIs (replacing Blotato)."""
import logging
from typing import Dict, List, Any

from features.oauth.youtube_publisher import publish_to_youtube
from features.publishing.storage import (
    get_connected_accounts,
    get_account_by_id,
    record_publish,
)

logger = logging.getLogger(__name__)


class PublishingService:
    """Service for publishing content to platforms via native APIs."""

    def __init__(self, user_id: str):
        self.user_id = user_id

    async def publish_video(
        self,
        file_path: str,
        title: str,
        description: str,
        platforms: List[str] = None,
        tags: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish video to connected platforms.
        Returns dict with results per platform.

        Args:
            file_path: Path to the video file
            title: Video title
            description: Video description
            platforms: List of platforms to publish to (default: all connected)
            tags: Optional list of tags

        Returns:
            Dict mapping platform name to result dict with success/error
        """
        if platforms is None:
            # Get all connected platforms
            accounts = await get_connected_accounts(self.user_id)
            platforms = list(set(a["platform"] for a in accounts))

        results = {}

        for platform in platforms:
            if platform == "youtube":
                # Get all YouTube accounts for this user
                youtube_accounts = await get_connected_accounts(self.user_id, "youtube")

                if not youtube_accounts:
                    results["youtube"] = {
                        "success": False,
                        "error": "No YouTube account connected"
                    }
                    continue

                # Publish to the first (or primary) YouTube account
                account = youtube_accounts[0]
                result = await publish_to_youtube(
                    account_id=account["id"],
                    video_path=file_path,
                    title=title,
                    description=description,
                    tags=tags,
                    user_id=self.user_id,
                )
                results["youtube"] = result

            elif platform == "instagram":
                # Phase 2: Instagram support
                results["instagram"] = {
                    "success": False,
                    "error": "Instagram not yet implemented"
                }
            elif platform == "tiktok":
                # Phase 2: TikTok support
                results["tiktok"] = {
                    "success": False,
                    "error": "TikTok not yet implemented"
                }
            else:
                results[platform] = {
                    "success": False,
                    "error": f"Unknown platform: {platform}"
                }

        return results

    async def publish_to_accounts(
        self,
        video_url: str = None,
        video_path: str = None,
        title: str = "",
        description: str = "",
        tags: List[str] = None,
        account_ids: List[str] = None,
        scheduled_post_id: str = None,
    ) -> Dict[str, Any]:
        """
        Publish video to specific accounts (for cross-posting).

        Args:
            video_url: URL to video (for scheduled posts)
            video_path: Local path to video file
            title: Video title
            description: Video description
            tags: Optional list of tags
            account_ids: List of account IDs to publish to
            scheduled_post_id: Optional ID of scheduled post (for tracking)

        Returns:
            Dict mapping account_id to result dict
        """
        if not account_ids:
            return {}

        # Use video_path if provided, otherwise we'd need to download from video_url
        # For now, require video_path for direct publishing
        if not video_path:
            if video_url:
                # TODO: Download video from URL to temp file
                logger.warning("video_url without video_path not yet supported")
                return {aid: {"success": False, "error": "video_path required"} for aid in account_ids}
            return {aid: {"success": False, "error": "No video provided"} for aid in account_ids}

        results = {}

        for account_id in account_ids:
            account = await get_account_by_id(account_id)
            if not account:
                results[account_id] = {"success": False, "error": "Account not found"}
                continue

            if account["user_id"] != self.user_id:
                results[account_id] = {"success": False, "error": "Not authorized"}
                continue

            platform = account["platform"]

            if platform == "youtube":
                result = await publish_to_youtube(
                    account_id=account_id,
                    video_path=video_path,
                    title=title,
                    description=description,
                    tags=tags,
                    user_id=self.user_id,
                    scheduled_post_id=scheduled_post_id,
                )
                results[account_id] = result
            else:
                results[account_id] = {
                    "success": False,
                    "error": f"Platform {platform} not yet implemented"
                }

        return results

    async def get_connected_platforms(self) -> List[str]:
        """Get list of connected platform names."""
        accounts = await get_connected_accounts(self.user_id)
        return list(set(a["platform"] for a in accounts))

    async def get_connected_accounts_list(self) -> List[Dict[str, Any]]:
        """Get list of all connected accounts with details."""
        accounts = await get_connected_accounts(self.user_id)
        return [
            {
                "id": a["id"],
                "platform": a["platform"],
                "account_name": a.get("account_name"),
                "account_image_url": a.get("account_image_url"),
                "connected_at": a.get("connected_at"),
            }
            for a in accounts
        ]

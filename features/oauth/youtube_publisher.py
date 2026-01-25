"""YouTube video publishing using stored OAuth credentials."""
import os
import logging
from typing import Optional, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

from features.publishing.storage import get_account_by_id, record_publish
from features.oauth.youtube import YouTubeOAuth

logger = logging.getLogger(__name__)


async def publish_to_youtube(
    account_id: str,
    video_path: str,
    title: str,
    description: str,
    tags: list = None,
    user_id: str = None,
    scheduled_post_id: str = None,
) -> Dict[str, Any]:
    """
    Publish video to YouTube using stored OAuth credentials.
    Returns dict with success status, video URL, or error.
    """
    # Get stored account/credentials
    account = await get_account_by_id(account_id)
    if not account:
        logger.error(f"No account found with id {account_id}")
        return {"success": False, "error": "Account not found"}

    if account["platform"] != "youtube":
        return {"success": False, "error": "Account is not a YouTube account"}

    # Ensure token is valid (auto-refresh if needed)
    try:
        access_token = await YouTubeOAuth.ensure_valid_token(account)
    except Exception as e:
        logger.error(f"Failed to refresh YouTube token: {e}")
        if user_id:
            await record_publish(
                user_id=user_id,
                account_id=account_id,
                platform="youtube",
                scheduled_post_id=scheduled_post_id,
                status="failed",
                error_message=f"Token refresh failed: {e}"
            )
        return {"success": False, "error": f"Token refresh failed: {e}"}

    # Build credentials object for Google API
    credentials = Credentials(
        token=access_token,
        refresh_token=account.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    )

    try:
        youtube = build("youtube", "v3", credentials=credentials)

        # Add #Shorts tag if not present and video is short-form
        if "#shorts" not in title.lower() and "#short" not in title.lower():
            title = f"{title} #Shorts"

        if tags is None:
            tags = ["shorts", "ai", "generated"]

        # Ensure #shorts is in tags for YouTube Shorts
        if "shorts" not in [t.lower() for t in tags]:
            tags.append("shorts")

        body = {
            "snippet": {
                "title": title[:100],  # YouTube title limit
                "description": description[:5000] if description else "",  # YouTube description limit
                "tags": tags[:500],  # YouTube has tag limits
                "categoryId": "22",  # People & Blogs
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            }
        }

        media = MediaFileUpload(
            video_path,
            chunksize=-1,
            resumable=True,
            mimetype="video/mp4"
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = request.execute()
        video_id = response["id"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        logger.info(f"Video uploaded to YouTube: {video_url}")

        # Record success
        if user_id:
            await record_publish(
                user_id=user_id,
                account_id=account_id,
                platform="youtube",
                scheduled_post_id=scheduled_post_id,
                platform_post_id=video_id,
                platform_post_url=video_url,
                status="success",
            )

        return {
            "success": True,
            "video_id": video_id,
            "url": video_url,
            "platform": "youtube",
            "account_name": account.get("account_name"),
        }

    except Exception as e:
        logger.error(f"YouTube upload failed: {e}")
        if user_id:
            await record_publish(
                user_id=user_id,
                account_id=account_id,
                platform="youtube",
                scheduled_post_id=scheduled_post_id,
                status="failed",
                error_message=str(e),
            )
        return {"success": False, "error": str(e)}

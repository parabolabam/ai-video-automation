"""YouTube OAuth implementation with auto-refresh."""
import os
import logging
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
import httpx

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


class YouTubeOAuth:
    """YouTube OAuth2 implementation."""

    @staticmethod
    def get_auth_url(redirect_uri: str, state: str) -> str:
        """Generate Google OAuth authorization URL."""
        client_id = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("YOUTUBE_CLIENT_ID")

        from urllib.parse import urlencode
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }

        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    @staticmethod
    async def exchange_code(code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        client_id = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("YOUTUBE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or os.getenv("YOUTUBE_CLIENT_SECRET")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                }
            )
            resp.raise_for_status()
            tokens = resp.json()

        # Get channel info to identify the connected account
        channel_info = await YouTubeOAuth.get_channel_info(tokens["access_token"])

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in", 3600),
            "platform_account_id": channel_info.get("id"),
            "account_name": channel_info.get("title"),
            "account_image_url": channel_info.get("thumbnail_url"),
        }

    @staticmethod
    async def refresh_token(refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired access token."""
        client_id = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("YOUTUBE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or os.getenv("YOUTUBE_CLIENT_SECRET")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                }
            )
            resp.raise_for_status()
            tokens = resp.json()

        return {
            "access_token": tokens["access_token"],
            "expires_in": tokens.get("expires_in", 3600),
        }

    @staticmethod
    async def get_channel_info(access_token: str) -> Dict[str, Any]:
        """Get YouTube channel info for display."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "snippet", "mine": "true"},
                headers={"Authorization": f"Bearer {access_token}"}
            )
            data = resp.json()
            if data.get("items"):
                item = data["items"][0]
                snippet = item.get("snippet", {})
                thumbnails = snippet.get("thumbnails", {})
                thumbnail_url = thumbnails.get("default", {}).get("url")
                return {
                    "id": item["id"],
                    "title": snippet.get("title", "Unknown Channel"),
                    "thumbnail_url": thumbnail_url,
                }
        return {}

    @staticmethod
    async def ensure_valid_token(account: Dict[str, Any]) -> str:
        """Ensure token is valid, refresh if needed. Returns valid access_token."""
        from features.publishing.storage import update_account_tokens

        expires_at = account.get("token_expires_at")
        if expires_at:
            if isinstance(expires_at, str):
                # Handle ISO format string
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))

            # Make sure we compare timezone-aware datetimes
            now = datetime.now(timezone.utc)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            # Refresh if expires within 5 minutes
            if expires_at <= now + timedelta(minutes=5):
                logger.info("YouTube token expired or expiring soon, refreshing...")
                refresh_token_value = account.get("refresh_token")
                if not refresh_token_value:
                    raise ValueError("No refresh token available")

                new_tokens = await YouTubeOAuth.refresh_token(refresh_token_value)
                await update_account_tokens(account["id"], new_tokens)
                return new_tokens["access_token"]

        return account["access_token"]

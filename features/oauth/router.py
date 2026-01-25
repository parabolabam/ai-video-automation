"""OAuth endpoints for connecting social accounts."""
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
import os
import secrets
import logging

from features.oauth.youtube import YouTubeOAuth
from features.publishing.storage import (
    save_connected_account,
    get_connected_accounts,
    delete_connected_account,
    get_account_by_id,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/oauth", tags=["oauth"])

# In-memory state storage (use Redis in production for multi-instance)
_oauth_states: dict = {}


@router.get("/youtube/authorize")
async def youtube_authorize(request: Request, user_id: str = Query(None)):
    """Generate YouTube OAuth URL and redirect user to Google login."""
    if not user_id:
        raise HTTPException(400, "user_id query parameter required")

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {"user_id": user_id, "platform": "youtube"}

    # Build redirect URI from request
    redirect_uri = str(request.url_for("youtube_callback"))
    auth_url = YouTubeOAuth.get_auth_url(redirect_uri, state)

    return RedirectResponse(auth_url)


@router.get("/youtube/callback")
async def youtube_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle YouTube OAuth callback, exchange code for tokens, save to database."""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Handle OAuth errors
    if error:
        logger.error(f"YouTube OAuth error: {error}")
        return RedirectResponse(f"{frontend_url}/settings?error={error}")

    if not code or not state:
        return RedirectResponse(f"{frontend_url}/settings?error=missing_params")

    if state not in _oauth_states:
        raise HTTPException(400, "Invalid or expired state parameter")

    state_data = _oauth_states.pop(state)
    user_id = state_data["user_id"]
    redirect_uri = str(request.url_for("youtube_callback"))

    try:
        tokens = await YouTubeOAuth.exchange_code(code, redirect_uri)
        account_id = await save_connected_account(user_id, "youtube", tokens)
        logger.info(f"YouTube connected for user {user_id}: {tokens.get('account_name')} (account_id: {account_id})")
    except Exception as e:
        logger.error(f"YouTube OAuth failed: {e}")
        return RedirectResponse(f"{frontend_url}/settings?error=youtube_failed")

    return RedirectResponse(f"{frontend_url}/settings?connected=youtube")


@router.get("/accounts")
async def list_accounts(user_id: str = Query(...), platform: str = Query(None)):
    """Get list of connected accounts for a user."""
    accounts = await get_connected_accounts(user_id, platform)
    return {
        "accounts": [
            {
                "id": a["id"],
                "platform": a["platform"],
                "account_name": a.get("account_name"),
                "account_image_url": a.get("account_image_url"),
                "connected_at": a.get("connected_at"),
                "is_active": a.get("is_active", True),
            }
            for a in accounts
        ]
    }


@router.delete("/accounts/{account_id}")
async def disconnect_account(account_id: str, user_id: str = Query(...)):
    """Disconnect a specific account."""
    # Verify ownership
    account = await get_account_by_id(account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    if account["user_id"] != user_id:
        raise HTTPException(403, "Not authorized to delete this account")

    await delete_connected_account(account_id)
    return {"status": "disconnected", "account_id": account_id}


@router.get("/status")
async def oauth_status(user_id: str = Query(...)):
    """Get summary of connected platforms for a user (for quick status check)."""
    accounts = await get_connected_accounts(user_id)

    # Group by platform
    platforms = {}
    for a in accounts:
        platform = a["platform"]
        if platform not in platforms:
            platforms[platform] = []
        platforms[platform].append({
            "id": a["id"],
            "account_name": a.get("account_name"),
            "connected_at": a.get("connected_at"),
        })

    return {
        "connected_platforms": list(platforms.keys()),
        "accounts_by_platform": platforms,
        "total_accounts": len(accounts),
    }

"""Storage for connected accounts, scheduled posts, and publish history."""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from supabase import create_client


def get_supabase():
    """Get Supabase client with service role key for backend operations."""
    url = os.getenv("SUPABASE_URL")
    # Use service key for backend - bypasses RLS
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY are required")
    return create_client(url, key)


# ============================================================
# CONNECTED ACCOUNTS
# ============================================================

async def save_connected_account(user_id: str, platform: str, tokens: Dict[str, Any]) -> str:
    """Save a new connected account. Returns account ID."""
    supabase = get_supabase()

    expires_at = None
    if tokens.get("expires_in"):
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens["expires_in"])

    data = {
        "user_id": user_id,
        "platform": platform,
        "platform_account_id": tokens["platform_account_id"],
        "account_name": tokens["account_name"],
        "account_image_url": tokens.get("account_image_url"),
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "token_expires_at": expires_at.isoformat() if expires_at else None,
    }

    # Upsert by unique constraint (update if same account reconnected)
    result = supabase.table("connected_accounts").upsert(
        data, on_conflict="user_id,platform,platform_account_id"
    ).execute()

    return result.data[0]["id"] if result.data else None


async def get_connected_accounts(user_id: str, platform: str = None) -> List[Dict[str, Any]]:
    """Get all connected accounts for a user, optionally filtered by platform."""
    supabase = get_supabase()
    query = supabase.table("connected_accounts").select("*").eq("user_id", user_id).eq("is_active", True)
    if platform:
        query = query.eq("platform", platform)
    result = query.order("connected_at", desc=True).execute()
    return result.data or []


async def get_account_by_id(account_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific account by ID."""
    supabase = get_supabase()
    result = supabase.table("connected_accounts").select("*").eq("id", account_id).single().execute()
    return result.data


async def update_account_tokens(account_id: str, tokens: Dict[str, Any]):
    """Update tokens after refresh."""
    supabase = get_supabase()

    expires_at = None
    if tokens.get("expires_in"):
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens["expires_in"])

    supabase.table("connected_accounts").update({
        "access_token": tokens["access_token"],
        "token_expires_at": expires_at.isoformat() if expires_at else None,
        "last_used_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", account_id).execute()


async def delete_connected_account(account_id: str):
    """Delete a connected account."""
    supabase = get_supabase()
    supabase.table("connected_accounts").delete().eq("id", account_id).execute()


# ============================================================
# SCHEDULED POSTS
# ============================================================

async def create_scheduled_post(
    user_id: str,
    video_url: str,
    title: str,
    description: str,
    target_account_ids: List[str],
    publish_at: datetime,
    tags: List[str] = None
) -> str:
    """Create a scheduled post. Returns post ID."""
    supabase = get_supabase()

    # Ensure publish_at is timezone-aware
    if publish_at.tzinfo is None:
        publish_at = publish_at.replace(tzinfo=timezone.utc)

    data = {
        "user_id": user_id,
        "video_url": video_url,
        "title": title,
        "description": description,
        "tags": tags or [],
        "target_account_ids": target_account_ids,
        "publish_at": publish_at.isoformat(),
        "status": "pending",
    }

    result = supabase.table("scheduled_posts").insert(data).execute()
    return result.data[0]["id"] if result.data else None


async def get_scheduled_posts(user_id: str, status: str = None) -> List[Dict[str, Any]]:
    """Get scheduled posts for a user."""
    supabase = get_supabase()
    query = supabase.table("scheduled_posts").select("*").eq("user_id", user_id)
    if status:
        query = query.eq("status", status)
    result = query.order("publish_at", desc=False).execute()
    return result.data or []


async def get_pending_posts_to_publish() -> List[Dict[str, Any]]:
    """Get posts ready to be published (publish_at <= now, status = pending)."""
    supabase = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    result = supabase.table("scheduled_posts").select("*").eq("status", "pending").lte("publish_at", now).execute()
    return result.data or []


async def update_post_status(post_id: str, status: str, error_message: str = None):
    """Update scheduled post status."""
    supabase = get_supabase()
    data = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if error_message:
        data["error_message"] = error_message
    supabase.table("scheduled_posts").update(data).eq("id", post_id).execute()


async def delete_scheduled_post(post_id: str):
    """Cancel/delete a scheduled post."""
    supabase = get_supabase()
    supabase.table("scheduled_posts").delete().eq("id", post_id).execute()


# ============================================================
# PUBLISH HISTORY
# ============================================================

async def record_publish(
    user_id: str,
    account_id: str,
    platform: str,
    scheduled_post_id: str = None,
    platform_post_id: str = None,
    platform_post_url: str = None,
    status: str = "success",
    error_message: str = None
):
    """Record a publish attempt."""
    supabase = get_supabase()

    data = {
        "user_id": user_id,
        "account_id": account_id,
        "platform": platform,
        "platform_post_id": platform_post_id,
        "platform_post_url": platform_post_url,
        "status": status,
        "error_message": error_message,
    }

    # Only include scheduled_post_id if it's provided
    if scheduled_post_id:
        data["scheduled_post_id"] = scheduled_post_id

    supabase.table("publish_history").insert(data).execute()


async def get_publish_history(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent publish history for a user."""
    supabase = get_supabase()
    result = supabase.table("publish_history").select("*").eq("user_id", user_id).order("published_at", desc=True).limit(limit).execute()
    return result.data or []

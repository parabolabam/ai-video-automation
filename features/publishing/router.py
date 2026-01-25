"""Publishing API endpoints for scheduling and cross-posting."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import logging

from features.publishing.storage import (
    get_connected_accounts,
    create_scheduled_post,
    get_scheduled_posts,
    delete_scheduled_post,
    get_publish_history,
)
from features.publishing.service import PublishingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/publish", tags=["publishing"])


class PublishRequest(BaseModel):
    """Request to publish video immediately."""
    video_path: str
    title: str
    description: str = ""
    tags: List[str] = []
    target_account_ids: List[str]  # Which accounts to publish to


class ScheduleRequest(BaseModel):
    """Request to schedule a post for later."""
    video_url: str
    title: str
    description: str = ""
    tags: List[str] = []
    target_account_ids: List[str]
    publish_at: datetime  # ISO format datetime


@router.post("")
async def publish_now(req: PublishRequest, user_id: str = Query(...)):
    """Publish video immediately to selected accounts (cross-posting)."""
    if not req.target_account_ids:
        raise HTTPException(400, "target_account_ids is required")

    service = PublishingService(user_id)
    results = await service.publish_to_accounts(
        video_path=req.video_path,
        title=req.title,
        description=req.description,
        tags=req.tags,
        account_ids=req.target_account_ids,
    )

    # Summarize results
    success_count = sum(1 for r in results.values() if r.get("success"))
    total_count = len(results)

    return {
        "results": results,
        "summary": {
            "success": success_count,
            "failed": total_count - success_count,
            "total": total_count,
        }
    }


@router.post("/schedule")
async def schedule_post(req: ScheduleRequest, user_id: str = Query(...)):
    """Schedule a post for later (cross-posting supported)."""
    if not req.target_account_ids:
        raise HTTPException(400, "target_account_ids is required")

    # Ensure publish_at is in the future
    now = datetime.now(timezone.utc)
    publish_at = req.publish_at
    if publish_at.tzinfo is None:
        publish_at = publish_at.replace(tzinfo=timezone.utc)

    if publish_at <= now:
        raise HTTPException(400, "publish_at must be in the future")

    # Verify all target accounts exist and belong to user
    accounts = await get_connected_accounts(user_id)
    account_ids_set = {a["id"] for a in accounts}
    invalid_ids = [aid for aid in req.target_account_ids if aid not in account_ids_set]
    if invalid_ids:
        raise HTTPException(400, f"Invalid account IDs: {invalid_ids}")

    post_id = await create_scheduled_post(
        user_id=user_id,
        video_url=req.video_url,
        title=req.title,
        description=req.description,
        target_account_ids=req.target_account_ids,
        publish_at=publish_at,
        tags=req.tags,
    )

    return {
        "scheduled": True,
        "post_id": post_id,
        "publish_at": publish_at.isoformat(),
        "target_accounts": len(req.target_account_ids),
    }


@router.get("/queue")
async def get_queue(user_id: str = Query(...), status: str = Query(None)):
    """Get scheduled posts queue."""
    posts = await get_scheduled_posts(user_id, status)
    return {"posts": posts, "count": len(posts)}


@router.delete("/queue/{post_id}")
async def cancel_scheduled(post_id: str, user_id: str = Query(...)):
    """Cancel a scheduled post."""
    # Get post to verify ownership
    posts = await get_scheduled_posts(user_id)
    post = next((p for p in posts if p["id"] == post_id), None)

    if not post:
        raise HTTPException(404, "Post not found or not owned by user")

    if post["status"] not in ["pending", "cancelled"]:
        raise HTTPException(400, f"Cannot cancel post with status: {post['status']}")

    await delete_scheduled_post(post_id)
    return {"cancelled": True, "post_id": post_id}


@router.get("/history")
async def get_history(user_id: str = Query(...), limit: int = Query(50)):
    """Get publish history."""
    history = await get_publish_history(user_id, limit)
    return {"history": history, "count": len(history)}


@router.get("/accounts")
async def get_accounts(user_id: str = Query(...)):
    """Get connected accounts for publishing (shortcut to oauth/accounts)."""
    accounts = await get_connected_accounts(user_id)
    return {
        "accounts": [
            {
                "id": a["id"],
                "platform": a["platform"],
                "account_name": a.get("account_name"),
                "account_image_url": a.get("account_image_url"),
            }
            for a in accounts
        ]
    }

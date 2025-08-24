#!/usr/bin/env python3 

# Optionally post to Instagram if env vars are present and a public video URL is provided
import os
import logging
from features.instagram.create_reel_container import create_reel_container
from features.instagram.publish_reel import publish_reel

logger = logging.getLogger(__name__)

async def instagram_upload(video_url: str, caption: str):    
    ig_user_id = os.getenv("IG_USER_ID")
    ig_access_token = os.getenv("IG_ACCESS_TOKEN")
    ig_video_url = video_url
    ig_caption = caption
    if ig_user_id and ig_access_token and ig_video_url:
        try:
            creation_id = await create_reel_container(
                ig_user_id, ig_access_token, ig_video_url, ig_caption
        )
            if creation_id:
                await publish_reel(ig_user_id, ig_access_token, creation_id)
        except Exception as e:
                logger.warning(f"Instagram upload skipped due to error: {e}")
   
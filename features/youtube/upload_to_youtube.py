#!/usr/bin/env python3
"""
Upload a video to YouTube as a Short
"""

import logging
import os
from typing import Optional, Any
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


def upload_to_youtube(youtube_service: Any, video_path: str, title: str, description: str) -> Optional[str]:
    """Upload video to YouTube using provided service. Return video URL or None."""
    logger = logging.getLogger(__name__)

    if not youtube_service:
        logger.warning("YouTube service not available. Skipping upload.")
        return None

    try:
        if "#shorts" not in title.lower():
            title = f"{title} #Shorts"
        if "#shorts" not in description.lower():
            description = f"{description}\n\n#Shorts #AIGenerated #VideoArt"

        logger.info(f"Uploading video to YouTube: {video_path}")
        body = {
            'snippet': {
                'title': title[:100],
                'description': description,
                'tags': ['shorts', 'ai', 'generated', 'art', 'creative'],
                'categoryId': '22',
                'defaultLanguage': 'en',
                'defaultAudioLanguage': 'en'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }

        media = MediaFileUpload(
            video_path,
            chunksize=-1,
            resumable=True,
            mimetype='video/mp4'
        )

        request = youtube_service.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        response = request.execute()
        video_id = response['id']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info(f"Video uploaded successfully: {video_url}")
        if video_url:
            logger.info(f"Upload successful: {video_url}")
            try:
                os.remove(video_path)
                logger.info(f"Removed local video file: {video_path}")
            except Exception as e:
                logger.warning(f"Failed to remove local video file: {e}")
        else:
            logger.error("YouTube upload failed")
        return video_url

    except HttpError as e:
        logger.error(f"YouTube API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to upload to YouTube: {e}")
        return None

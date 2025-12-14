import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from features.blotato.client import BlotatoClient
from features.kie.poll_kie_status import poll_kie_status_for_url

logger = logging.getLogger(__name__)

class PublishingService:
    """Service for publishing content to platforms via Blotato."""
    
    def __init__(self, api_key: str):
        self.client = BlotatoClient(api_key=api_key)
        
    async def publish_video(
        self, 
        task_id: Optional[str] = None,
        file_path: Optional[str] = None,
        post_text: str = "", 
        scheduled_time_iso: Optional[str] = None
    ) -> bool:
        """Publish video (from task_id URL or local file) to configured targets."""
        
        media_url = None
        uploaded = None
        
        # 1. Upload to Blotato (either from URL or local file)
        try:
            if file_path:
                logger.info(f"Uploading local file to Blotato via Bridge: {file_path}")
                # Blotato doesn't accept file uploads, so we bridge via file.io
                bridge_url = await self._upload_to_bridge(file_path)
                if not bridge_url:
                    logger.error("Bridge upload failed")
                    return False
                    
                logger.info(f"Bridge URL obtained: {bridge_url}")
                uploaded = await self.client.upload_media(url=bridge_url)
            elif task_id:
                # Resolve media URL from Kie
                media_url = await poll_kie_status_for_url(task_id)
                if not media_url:
                    logger.error("Failed to obtain Kie media URL from task_id")
                    return False
                logger.info(f"Uploading to Blotato via URL: {media_url}")
                uploaded = await self.client.upload_media(url=media_url)
            else:
                logger.error("Either task_id or file_path must be provided")
                return False
                
            logger.info(f"Uploaded media to Blotato: {uploaded}")
        except Exception as e:
            logger.error(f"Failed to upload media to Blotato: {e}")
            return False
            
        hosted_media_url = None
        if isinstance(uploaded, dict):
             hosted_media_url = (
                uploaded.get("url")
                or uploaded.get("mediaUrl")
                or uploaded.get("data", {}).get("url")
            )
            
        if not hosted_media_url:
            logger.error("Upload to Blotato did not return a media URL")
            return False
            
        logger.info("Blotato hosted media URL resolved")
        
        # 3. Publish to targets
        targets_raw = os.getenv("BLOTATO_TARGETS")
        if not targets_raw:
            logger.error("BLOTATO_TARGETS is not set")
            return False
            
        try:
            targets_list = json.loads(targets_raw)
            if not isinstance(targets_list, list):
                raise ValueError("BLOTATO_TARGETS must be a list")
        except Exception as e:
            logger.error(f"Failed to parse BLOTATO_TARGETS: {e}")
            return False
            
        # Deduplication logic
        deduped_targets = self._deduplicate_targets(targets_list)
        posted_keys: Set[Tuple[str, str, str, str]] = set()
        
        tasks = []
        for target in deduped_targets:
            tasks.append(
                self._post_one(
                    hosted_media_url=hosted_media_url,
                    post_text=post_text,
                    scheduled_time_iso=scheduled_time_iso,
                    target_cfg=target,
                    posted_keys=posted_keys
                )
            )
            
        if tasks:
            results = await asyncio.gather(*tasks)
            if not all(results):
                logger.error("One or more platform posts failed")
                return False
                
        return True

    def _deduplicate_targets(self, targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped = []
        seen = set()
        for t in targets:
            key = (str(t.get("platform", "")).lower(), str(t.get("pageId") or ""))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(t)
        return deduped

    async def _upload_to_bridge(self, file_path: str) -> Optional[str]:
        """Upload file to ephemeral host (tmpfiles.org) to get a public URL for Blotato."""
        import aiohttp
        try:
            url = "https://tmpfiles.org/api/v1/upload"
            filename = os.path.basename(file_path)
            
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('file', open(file_path, 'rb'), filename=filename)
                
                async with session.post(url, data=data) as resp:
                    if resp.status != 200:
                        logger.error(f"Bridge upload failed: {resp.status} - {await resp.text()}")
                        return None
                        
                    result = await resp.json()
                    page_url = result.get("data", {}).get("url")
                    
                    if page_url:
                        # Convert to direct link for Blotato to consume
                        # https://tmpfiles.org/123/file.mp4 -> https://tmpfiles.org/dl/123/file.mp4
                        direct_url = page_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                        return direct_url
                        
                    logger.error(f"Bridge upload error (no url): {result}")
                    return None
        except Exception as e:
            logger.error(f"Bridge upload exception: {e}")
            return None

    async def _post_one(
        self,
        hosted_media_url: str,
        post_text: str,
        scheduled_time_iso: Optional[str],
        target_cfg: Dict[str, Any],
        posted_keys: Set[Tuple[str, str, str, str]],
    ) -> bool:
        """Publish to a single target."""
        platform = str(target_cfg.get("platform", "")).lower()
        page_id = target_cfg.get("pageId")
        account_id = None
        
        if platform == "tiktok":
            account_id = os.getenv("TIKTOK_ACCOUNT_ID")
        elif platform == "youtube":
            account_id = os.getenv("BLOTATO_ACCOUNT_ID_YOUTUBE")
        elif platform == "instagram":
            account_id = os.getenv("BLOTATO_ACCOUNT_ID_INSTAGRAM")
            
        if not platform:
            logger.warning(f"Skipping target missing platform: {target_cfg}")
            return False
            
        dedup_key = (platform, str(page_id or ""), str(account_id or ""), hosted_media_url)
        if dedup_key in posted_keys:
            return True
            
        try:
            if platform == "youtube":
                resp = await self.client.publish_youtube_post(
                    account_id=account_id,
                    text=post_text,
                    media_urls=[hosted_media_url],
                    page_id=page_id,
                    scheduled_time_iso=scheduled_time_iso,
                )
            elif platform == "instagram":
                resp = await self.client.publish_instagram_post(
                    account_id=account_id,
                    text=post_text,
                    media_urls=[hosted_media_url],
                    page_id=page_id,
                    scheduled_time_iso=scheduled_time_iso,
                )
            else:
                resp = await self.client.publish_tiktok_post(
                    account_id=account_id,
                    text=post_text,
                    media_urls=[hosted_media_url],
                    page_id=page_id,
                    scheduled_time_iso=scheduled_time_iso,
                )
            
            posted_keys.add(dedup_key)
            logger.info(f"Published via Blotato to {platform}: {resp}")
            return True
        except Exception as e:
            logger.error(f"Blotato post failed for {platform}: {e}")
            raise RuntimeError(f"Publish failed for {platform}") from e

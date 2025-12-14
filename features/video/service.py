import logging
import os
from typing import List, Optional, Tuple

from features.kie.video_apis import VideoGenerationAPI
from features.kie.poll_with_task_id import poll_with_task_id
from features.video.stitcher import stitch_videos

logger = logging.getLogger(__name__)

class VideoGenerationService:
    """Service for generating videos using Kie.ai (including multi-scene)."""
    
    def __init__(self):
        self.video_api = VideoGenerationAPI("kie")

    async def retrieve_video(self, task_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Retrieve a video from an existing task ID.
        
        Returns:
            (video_path, task_id)
        """
        logger.info(f"Retrieving video for existing taskId: {task_id}")
        video_path = await poll_with_task_id(task_id)
        return video_path, task_id
        
    async def generate_video(self, prompt: str, scenes: Optional[List[str]] = None) -> Tuple[Optional[str], Optional[str]]:
        """Generate a video, handling either single prompt or multiple scenes.
        
        Args:
            prompt: Base prompt (used for single scene)
            scenes: List of scene prompts (used for extended mode)
            
        Returns:
            (video_path, task_id) or (None, None) on failure
        """
        duration = int(os.getenv("VIDEO_DURATION", 8))
        quality = os.getenv("VIDEO_QUALITY", "fast").lower()
        
        if scenes and len(scenes) > 1:
            return await self._generate_multi_scene_video(scenes, duration, quality)
        
        # Single clip generation
        logger.info("Generating single video clip...")
        task_id = await self.video_api.request_kie_task_id(prompt, duration, quality)
        if not task_id:
            logger.error("Failed to obtain Kie taskId")
            return None, None
            
        logger.info(f"Obtained Kie taskId: {task_id}")
        video_path = await poll_with_task_id(task_id)
        return video_path, task_id

    async def _generate_multi_scene_video(self, scenes: List[str], duration: int, quality: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate multiple scenes using Kie Extend API and stitch them.
        
        Returns:
            (stitched_video_path, last_task_id)
        """
        logger.info(f"Generating {len(scenes)} scenes using Kie extend API...")
        
        clips: List[str] = []
        
        # Step 1: Generate the first scene
        logger.info(f"Scene 1: Generating initial video with prompt: {scenes[0][:100]}...")
        current_task_id = await self.video_api.request_kie_task_id(scenes[0], duration, quality)
        if not current_task_id:
            logger.error(f"Failed to generate first scene. Prompt was: {scenes[0]}")
            return None, None
        
        # Wait for first scene to complete
        first_video = await poll_with_task_id(current_task_id)
        if not first_video:
            logger.error("Failed to download first scene")
            return None, None
            
        logger.info(f"Scene 1 complete: {current_task_id}")
        clips.append(first_video)
        
        # Step 2: Extend with each subsequent scene
        for i, scene_prompt in enumerate(scenes[1:], start=2):
            logger.info(f"Scene {i}/{len(scenes)}: Extending video with prompt: {scene_prompt[:100]}...")
            
            # Use extend API to add new content (generates next segment)
            new_task_id = await self.video_api.extend_kie_video(current_task_id, scene_prompt)
            if not new_task_id:
                logger.error(f"Failed to extend scene {i}, prompt: {scene_prompt}")
                break
            
            # Wait for extension to complete
            extended_video = await poll_with_task_id(new_task_id)
            if not extended_video:
                logger.error(f"Failed to download extended scene {i}")
                break
                
            clips.append(extended_video)
            current_task_id = new_task_id
            logger.info(f"Scene {i} complete: {new_task_id}")
        
        if len(clips) > 1:
            logger.info(f"Stitching {len(clips)} extended clips...")
            try:
                stitched_video = await stitch_videos(clips)
                
                # Clean up intermediate clips
                for clip in clips:
                    try:
                        if clip != stitched_video and os.path.exists(clip):
                            os.remove(clip)
                    except Exception as e:
                        logger.warning(f"Failed to remove intermediate clip {clip}: {e}")
                        
                return stitched_video, current_task_id
            except Exception as e:
                logger.error(f"Stitching failed: {e}")
                return clips[0], current_task_id # Fallback
            
        return clips[0], current_task_id

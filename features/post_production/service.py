import logging
import os
from typing import Optional

from features.video.composer import compose_video_with_audio, get_video_duration
from features.video.subtitles import burn_subtitles

logger = logging.getLogger(__name__)

class PostProductionService:
    """Service for post-production (composition, subtitles)."""
    
    async def process_video(
        self, 
        video_path: str, 
        audio_path: str, 
        voiceover_script: Optional[str] = None
    ) -> str:
        """Compose video with audio and optionally burn subtitles.
        
        Args:
            video_path: Path to the raw video
            audio_path: Path to the voiceover audio
            voiceover_script: Script text for subtitles (optional)
            
        Returns:
            Path to the final processed video
        """
        # 1. Compose with audio
        logger.info("Composing video with audio...")
        composed_path = await compose_video_with_audio(video_path, audio_path)
        
        # Clean up raw video/audio if composition succeeded
        try:
            if video_path != composed_path and os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception as e:
            logger.warning(f"Failed to clean up pre-composition files: {e}")
            
        final_path = composed_path
        
        # 2. Burn subtitles if enabled and script provided
        enable_subtitles = os.getenv("ENABLE_SUBTITLES", "true").lower() == "true"
        if enable_subtitles and voiceover_script:
            logger.info("Burning subtitles into video...")
            try:
                # Get ACTUAL video duration
                actual_duration = await get_video_duration(final_path)
                logger.debug(f"Actual video duration: {actual_duration}s")
                
                video_before_subs = final_path
                subtitle_path = await burn_subtitles(
                    video_path=final_path,
                    script=voiceover_script,
                    total_duration=actual_duration,
                    font_size=int(os.getenv("SUBTITLE_FONT_SIZE", "14")),
                    words_per_subtitle=int(os.getenv("SUBTITLE_WORDS_PER_LINE", "8")),
                )
                logger.info(f"Subtitles burned: {subtitle_path}")
                final_path = subtitle_path
                
                # Clean up video without subtitles
                if final_path != video_before_subs and os.path.exists(video_before_subs):
                    try:
                        os.remove(video_before_subs)
                    except Exception as e:
                        logger.warning(f"Failed to clean up pre-subtitle video: {e}")
            except Exception as e:
                logger.error(f"Subtitle burn failed: {e}")
                # Continue with composed video without subtitles
        
        return final_path

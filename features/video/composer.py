#!/usr/bin/env python3
"""
Video composition utilities using FFmpeg.

Combines video and audio tracks to create final output.
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _check_ffmpeg() -> bool:
    """Check if FFmpeg is available."""
    return shutil.which("ffmpeg") is not None


async def compose_video_with_audio(
    video_path: str,
    audio_path: str,
    output_path: Optional[str] = None,
) -> str:
    """Merge audio track with video using FFmpeg.
    
    Args:
        video_path: Path to the video file
        audio_path: Path to the audio file (voiceover)
        output_path: Path for output file (auto-generated if not provided)
        
    Returns:
        Path to the composed video with audio
        
    Raises:
        RuntimeError: If composition fails
    """
    if not _check_ffmpeg():
        raise RuntimeError("FFmpeg is not installed or not in PATH")
    
    # Validate inputs
    if not os.path.exists(video_path):
        raise RuntimeError(f"Video file not found: {video_path}")
    if not os.path.exists(audio_path):
        raise RuntimeError(f"Audio file not found: {audio_path}")
    
    # Generate output path if not provided
    if output_path is None:
        video_dir = Path(video_path).parent
        video_stem = Path(video_path).stem
        output_path = str(video_dir / f"{video_stem}_with_audio.mp4")
    
    logger.info(f"Composing video with audio:")
    logger.info(f"  Video: {video_path}")
    logger.info(f"  Audio: {audio_path}")
    logger.info(f"  Output: {output_path}")
    
    # FFmpeg command:
    # -i video: input video
    # -i audio: input audio
    # -c:v copy: copy video stream (no re-encoding)
    # -c:a aac: encode audio as AAC
    # -map 0:v: use video from first input
    # -map 1:a: use audio from second input
    # -shortest: match length to shortest stream
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"FFmpeg failed: {error_msg}")
            raise RuntimeError(f"FFmpeg composition failed: {error_msg}")
        
        logger.info(f"Video composed successfully: {output_path}")
        return output_path
        
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        logger.error(f"Failed to compose video: {e}")
        raise RuntimeError(f"Video composition failed: {e}") from e


async def get_video_duration(video_path: str) -> float:
    """Get the duration of a video file in seconds.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Duration in seconds
    """
    if not _check_ffmpeg():
        raise RuntimeError("FFmpeg/ffprobe is not installed")
    
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {stderr.decode()}")
        
        duration = float(stdout.decode().strip())
        logger.debug(f"Video duration: {duration}s")
        return duration
        
    except Exception as e:
        logger.error(f"Failed to get video duration: {e}")
        raise RuntimeError(f"Failed to get video duration: {e}") from e


async def get_audio_duration(audio_path: str) -> float:
    """Get the duration of an audio file in seconds."""
    return await get_video_duration(audio_path)  # Same ffprobe command works

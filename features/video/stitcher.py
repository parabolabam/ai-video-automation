#!/usr/bin/env python3
"""
Video stitching utilities using FFmpeg.

Concatenates multiple video clips into a single output.
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


async def stitch_videos(
    clips: list[str],
    output_path: Optional[str] = None,
    transition: str = "none",
) -> str:
    """Concatenate multiple video clips into one using FFmpeg.
    
    Args:
        clips: List of paths to video clips (in order)
        output_path: Path for output file (auto-generated if not provided)
        transition: Transition type ('none', 'fade', 'dissolve') - future use
        
    Returns:
        Path to the stitched video
        
    Raises:
        RuntimeError: If stitching fails
    """
    if not clips:
        raise RuntimeError("No clips provided for stitching")
    
    if len(clips) == 1:
        logger.info("Only one clip provided, no stitching needed")
        return clips[0]
    
    # Validate all clips exist
    for clip in clips:
        if not os.path.exists(clip):
            raise RuntimeError(f"Clip not found: {clip}")
    
    # Generate output path
    if output_path is None:
        first_clip = Path(clips[0])
        output_path = str(first_clip.parent / f"stitched_{first_clip.stem}.mp4")
    
    logger.info(f"Stitching {len(clips)} clips into: {output_path}")
    
    # Create concat file for FFmpeg
    concat_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.txt', delete=False
    )
    try:
        for clip in clips:
            # FFmpeg concat requires escaped paths
            concat_file.write(f"file '{clip}'\n")
        concat_file.close()
        
        # FFmpeg concat command
        # Using concat demuxer for same-codec files (fast, no re-encoding)
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file.name,
            "-c", "copy",  # Copy streams without re-encoding
            output_path,
        ]
        
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"FFmpeg stitching failed: {error_msg}")
            raise RuntimeError(f"Video stitching failed: {error_msg}")
        
        logger.info(f"Successfully stitched {len(clips)} clips: {output_path}")
        return output_path
        
    finally:
        # Clean up temp file
        try:
            os.unlink(concat_file.name)
        except Exception:
            pass


async def stitch_with_transitions(
    clips: list[str],
    output_path: Optional[str] = None,
    fade_duration: float = 0.5,
) -> str:
    """Stitch videos with crossfade transitions (requires re-encoding).
    
    This is slower than simple concat but produces smoother results.
    
    Args:
        clips: List of paths to video clips
        output_path: Output path
        fade_duration: Duration of crossfade in seconds
        
    Returns:
        Path to stitched video
    """
    if not clips:
        raise RuntimeError("No clips provided")
    
    if len(clips) == 1:
        return clips[0]
    
    if output_path is None:
        first_clip = Path(clips[0])
        output_path = str(first_clip.parent / f"stitched_fade_{first_clip.stem}.mp4")
    
    logger.info(f"Stitching {len(clips)} clips with {fade_duration}s crossfade")
    
    # Build complex filter for crossfade
    # This requires re-encoding but gives smooth transitions
    inputs = []
    for clip in clips:
        inputs.extend(["-i", clip])
    
    # Build filter complex for xfade
    filter_parts = []
    n = len(clips)
    
    if n == 2:
        # Simple case: 2 clips
        filter_complex = f"[0:v][1:v]xfade=transition=fade:duration={fade_duration}[v];[0:a][1:a]acrossfade=d={fade_duration}[a]"
    else:
        # Multiple clips: chain xfades
        current_v = "[0:v]"
        current_a = "[0:a]"
        
        for i in range(1, n):
            out_v = f"[v{i}]" if i < n - 1 else "[v]"
            out_a = f"[a{i}]" if i < n - 1 else "[a]"
            
            filter_parts.append(
                f"{current_v}[{i}:v]xfade=transition=fade:duration={fade_duration}{out_v}"
            )
            filter_parts.append(
                f"{current_a}[{i}:a]acrossfade=d={fade_duration}{out_a}"
            )
            
            current_v = out_v
            current_a = out_a
        
        filter_complex = ";".join(filter_parts)
    
    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
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
            logger.error(f"FFmpeg crossfade failed: {error_msg}")
            # Fall back to simple concat
            logger.info("Falling back to simple concat...")
            return await stitch_videos(clips, output_path)
        
        logger.info(f"Successfully stitched with crossfade: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Crossfade failed: {e}, using simple concat")
        return await stitch_videos(clips, output_path)

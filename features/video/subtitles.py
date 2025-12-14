#!/usr/bin/env python3
"""
Subtitle generation and video overlay using FFmpeg.

Creates timed subtitles from voiceover script and burns them into video.
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Subtitle styling
DEFAULT_FONT_SIZE = 14
DEFAULT_FONT_COLOR = "white"
DEFAULT_OUTLINE_COLOR = "black"
DEFAULT_OUTLINE_WIDTH = 2


def generate_srt_from_script(
    script: str,
    total_duration: float,
    words_per_subtitle: int = 8,
) -> str:
    """Generate SRT subtitle content from a script.
    
    Splits the script into chunks and assigns timing based on total duration.
    
    Args:
        script: The voiceover script text
        total_duration: Total video duration in seconds
        words_per_subtitle: Words per subtitle chunk
        
    Returns:
        SRT formatted string
    """
    # Clean the script - remove [Pause] markers
    clean_script = script.replace("[Pause]", "").replace("  ", " ").strip()
    
    words = clean_script.split()
    if not words:
        return ""
    
    # Create chunks of words
    chunks = []
    for i in range(0, len(words), words_per_subtitle):
        chunk = " ".join(words[i:i + words_per_subtitle])
        chunks.append(chunk)
    
    if not chunks:
        return ""
    
    # Calculate timing for each chunk
    duration_per_chunk = total_duration / len(chunks)
    
    srt_lines = []
    for i, chunk in enumerate(chunks):
        start_time = i * duration_per_chunk
        end_time = (i + 1) * duration_per_chunk
        
        # Format as SRT timestamp (HH:MM:SS,mmm)
        start_str = _format_srt_time(start_time)
        end_str = _format_srt_time(end_time)
        
        srt_lines.append(f"{i + 1}")
        srt_lines.append(f"{start_str} --> {end_str}")
        srt_lines.append(chunk)
        srt_lines.append("")  # Empty line between entries
    
    return "\n".join(srt_lines)


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


async def burn_subtitles(
    video_path: str,
    script: str,
    total_duration: float,
    output_path: Optional[str] = None,
    font_size: int = DEFAULT_FONT_SIZE,
    font_color: str = DEFAULT_FONT_COLOR,
    words_per_subtitle: int = 8,
) -> str:
    """Burn subtitles into video using FFmpeg.
    
    Args:
        video_path: Path to input video
        script: Voiceover script text
        total_duration: Video duration in seconds
        output_path: Output path (auto-generated if not provided)
        font_size: Subtitle font size
        font_color: Subtitle text color
        words_per_subtitle: Words per subtitle line
        
    Returns:
        Path to video with burned subtitles
    """
    if not os.path.exists(video_path):
        raise RuntimeError(f"Video not found: {video_path}")
    
    # Generate SRT content
    srt_content = generate_srt_from_script(
        script, total_duration, words_per_subtitle
    )
    
    if not srt_content:
        logger.warning("No subtitles generated, returning original video")
        return video_path
    
    # Write SRT to temp file
    srt_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.srt', delete=False, encoding='utf-8'
    )
    srt_file.write(srt_content)
    srt_file.close()
    
    logger.info(f"Generated SRT file: {srt_file.name}")
    
    # Generate output path
    if output_path is None:
        video_stem = Path(video_path).stem
        video_dir = Path(video_path).parent
        output_path = str(video_dir / f"{video_stem}_subtitled.mp4")
    
    logger.info(f"Burning subtitles into video: {output_path}")
    
    # FFmpeg command to burn subtitles
    # Using subtitles filter with force_style for customization
    style = f"FontSize={font_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline={DEFAULT_OUTLINE_WIDTH},Alignment=2"
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vf", f"subtitles={srt_file.name}:force_style='{style}'",
        "-c:v", "libx264", # Explicitly set encoder
        "-preset", "veryfast", # Faster encoding uses less memory/CPU time
        "-threads", "2", # Limit threads to reduce memory overhead per thread
        "-max_muxing_queue_size", "4096", # Prevent OOM on muxing queue
        "-c:a", "copy",
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
            logger.error(f"FFmpeg subtitle burn failed: {error_msg}")
            # Return original video on failure
            return video_path
        
        logger.info(f"Subtitles burned successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Subtitle burn failed: {e}")
        return video_path
    finally:
        # Clean up temp SRT file
        try:
            os.unlink(srt_file.name)
        except Exception:
            pass


async def save_srt_file(
    script: str,
    total_duration: float,
    output_path: str,
    words_per_subtitle: int = 5,
) -> str:
    """Save subtitles as separate SRT file for platforms that support it.
    
    Args:
        script: Voiceover script
        total_duration: Video duration
        output_path: Path to save SRT file
        words_per_subtitle: Words per line
        
    Returns:
        Path to saved SRT file
    """
    srt_content = generate_srt_from_script(
        script, total_duration, words_per_subtitle
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    logger.info(f"SRT file saved: {output_path}")
    return output_path

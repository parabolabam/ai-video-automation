#!/usr/bin/env python3
"""
Project-wide constants for YouTube scopes
"""


def youtube_scopes() -> list[str]:
    """Return YouTube API OAuth scopes."""
    return ['https://www.googleapis.com/auth/youtube.upload']

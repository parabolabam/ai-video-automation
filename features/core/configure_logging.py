#!/usr/bin/env python3
"""
Logging configuration for the AI Video Automation project
"""

import logging


_LOGGING_CONFIGURED = False


def configure_logging() -> None:
    """Configure root logging handlers and format.

    Safe to call multiple times; only configures once.
    """
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('video_automation.log'),
            logging.StreamHandler()
        ]
    )
    _LOGGING_CONFIGURED = True

#!/usr/bin/env python3
"""
Environment loader for .env variables
"""

from dotenv import load_dotenv


def load_env() -> None:
    """Load environment variables from .env if present."""
    load_dotenv()

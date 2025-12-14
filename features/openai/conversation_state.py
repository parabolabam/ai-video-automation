#!/usr/bin/env python3
"""
Conversation state management using Supabase.

Stores OpenAI response IDs to enable continuous conversation across cron job runs.
OpenAI maintains the full conversation context server-side, we just store the response ID.
"""

import logging
import os
from typing import Optional

from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Table and key constants
TABLE_NAME = "conversation_state"
STATE_KEY = "video_prompt_generator"


def _get_supabase_client() -> Client:
    """Create and return a Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    
    return create_client(url, key)


def load_previous_response_id() -> Optional[str]:
    """Load the previous response ID from Supabase.
    
    Returns:
        The previous response ID if available, None otherwise.
    """
    try:
        client = _get_supabase_client()
        
        result = (
            client.table(TABLE_NAME)
            .select("response_id")
            .eq("key", STATE_KEY)
            .limit(1)
            .execute()
        )
        
        if result.data and len(result.data) > 0:
            response_id = result.data[0].get("response_id")
            if response_id:
                logger.info(f"Loaded previous response ID: {response_id[:20]}...")
                return response_id
        
        logger.debug("No previous response ID found in Supabase")
        return None
        
    except Exception as e:
        logger.warning(f"Failed to load response ID from Supabase: {e}")
        return None


def save_response_id(response_id: str) -> None:
    """Save the response ID to Supabase for the next run.
    
    Uses upsert to insert or update the record.
    
    Args:
        response_id: The response ID from OpenAI to store.
    """
    try:
        client = _get_supabase_client()
        
        # Upsert: insert if not exists, update if exists
        client.table(TABLE_NAME).upsert({
            "key": STATE_KEY,
            "response_id": response_id,
        }, on_conflict="key").execute()
        
        logger.info(f"Saved response ID to Supabase: {response_id[:20]}...")
        
    except Exception as e:
        logger.error(f"Failed to save response ID to Supabase: {e}")


def clear_conversation_state() -> None:
    """Clear the conversation state to start fresh.
    
    Use this if the conversation needs to be reset (e.g., context too long).
    """
    try:
        client = _get_supabase_client()
        
        client.table(TABLE_NAME).delete().eq("key", STATE_KEY).execute()
        logger.info("Cleared conversation state from Supabase")
        
    except Exception as e:
        logger.error(f"Failed to clear conversation state: {e}")

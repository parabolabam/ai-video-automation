#!/usr/bin/env python3
"""
Seed the database with a sample 'Science Research' workflow for testing the platform.

Creates:
1. A test user (if not exists)
2. A 'Science Research' workflow
3. Researcher and Evaluator agents
4. Connections between them
"""

import asyncio
import logging
import os
from uuid import uuid4

from dotenv import load_dotenv
from supabase import create_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed():
    load_dotenv()
    
    import argparse
    parser = argparse.ArgumentParser(description="Seed DB")
    parser.add_argument("--user-id", help="Existing Supabase Auth User ID to use")
    args = parser.parse_args()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        logger.error("SUPABASE_URL/KEY missing")
        return

    supabase = create_client(url, key)
    
    logger.info("Starting seed...")

    # 1. Get or Create User via Auth
    user_id = args.user_id
    
    if not user_id:
        # We need a valid auth user to respect the FK constraint on profiles.
        # Using a realistic looking email to pass common regex checks
        email = "video.auto.test.user@gmail.com" 
        password = "ProcessUser123!" # Stronger password just in case
        
        try:
            logger.info(f"Attempting to sign up/sign in test user: {email}")
            # Try to sign up
            auth_resp = supabase.auth.sign_up({"email": email, "password": password})
            if auth_resp.user:
                user_id = auth_resp.user.id
                logger.info(f"Created/Found auth user ID: {user_id}")
            else:
                # Maybe already exists, try sign in
                try:
                    signin_resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if signin_resp.user:
                        user_id = signin_resp.user.id
                        logger.info(f"Signed in as existing user ID: {user_id}")
                except Exception as e:
                    logger.warning(f"Sign in failed: {e}")
                    
        except Exception as e:
            logger.warning(f"Auth operation failed: {e}")

    if not user_id:
        # Fallback: Ask user/environment variable if automatic auth fails
        logger.warning("Could not create/get auth user automatically.")
        user_id = os.getenv("TEST_USER_ID")
        if not user_id:
             # Try to find 'any' profile as last resort
            existing_profiles = supabase.table("profiles").select("id").limit(1).execute()
            if existing_profiles.data:
                user_id = existing_profiles.data[0]["id"]
                logger.info(f"Using first found existing profile ID: {user_id}")
            else:
                logger.error("No valid user ID available. Please run with --user-id <UUID> of an existing user.")
                return

    # Check/Create Profile
    try:
        # Upsert profile to ensure it exists
        supabase.table("profiles").upsert({
            "id": user_id, 
            "full_name": "Test Seed User",
            "avatar_url": ""
        }).execute()
        logger.info(f"Ensured profile exists for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to upsert profile: {e}")
        return

    # 2. Create Workflow
    wf_id = str(uuid4())
    logger.info(f"Creating Workflow {wf_id}...")
    supabase.table("workflows").insert({
        "id": wf_id,
        "user_id": user_id,
        "name": "Science Research Flow",
        "description": "Auto-generated test flow"
    }).execute()

    # 3. Create Agents
    researcher_id = str(uuid4())
    logger.info("Creating Researcher Agent...")
    supabase.table("agents").insert({
        "id": researcher_id,
        "workflow_id": wf_id,
        "name": "Researcher",
        "role": "Researcher",
        "model": "gpt-4o",
        "system_instructions": "You are a science researcher. Find 1 interesting fact about: {{input}}",
        "tools": ["web_search"]
    }).execute()
    
    evaluator_id = str(uuid4())
    logger.info("Creating Evaluator Agent...")
    supabase.table("agents").insert({
        "id": evaluator_id,
        "workflow_id": wf_id,
        "name": "Evaluator",
        "role": "Evaluator",
        "model": "gpt-4o",
        "system_instructions": "Verify this fact for accuracy: {{input}}",
        "tools": ["fact_check"]
    }).execute()

    # 4. Connect them
    logger.info("Connecting Agents...")
    
    # Start -> Researcher
    supabase.table("workflow_connections").insert({
        "workflow_id": wf_id,
        "from_agent_id": None, # Start
        "to_agent_id": researcher_id,
        "description": "Start"
    }).execute()
    
    # Researcher -> Evaluator
    supabase.table("workflow_connections").insert({
        "workflow_id": wf_id,
        "from_agent_id": researcher_id,
        "to_agent_id": evaluator_id,
        "description": "Verify"
    }).execute()

    logger.info("Seed complete!")
    print(f"\nRUN THIS COMMAND TO TEST:\npython3 -m features.platform.cli --workflow {wf_id} --user {user_id} --input 'Black holes'")

if __name__ == "__main__":
    asyncio.run(seed())

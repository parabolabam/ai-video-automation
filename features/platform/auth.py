"""
Authentication utilities for FastAPI backend using Supabase.
"""

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Service role key for backend

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    logger.warning("Supabase credentials not configured. Authentication will be disabled.")
    supabase: Optional[Client] = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> dict:
    """
    Verify the JWT token from Supabase and return the user.

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        dict: User data from Supabase auth

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not supabase:
        # If Supabase not configured, reject all requests
        logger.error("Authentication failed - Supabase not configured")
        raise HTTPException(
            status_code=500,
            detail="Authentication service not configured. Please contact administrator.",
        )

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Verify the JWT token with Supabase
        response = supabase.auth.get_user(token)

        if not response or not response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = response.user
        return {
            "id": user.id,
            "email": user.email,
            "user_metadata": user.user_metadata,
        }

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[dict]:
    """
    Optional authentication - returns user if authenticated, None otherwise.
    Useful for endpoints that work both with and without authentication.
    """
    if not credentials or not supabase:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def verify_user_access(user_id: str, authenticated_user: dict) -> bool:
    """
    Verify that the authenticated user has access to resources for the given user_id.

    Args:
        user_id: The user_id from the request
        authenticated_user: The authenticated user from get_current_user

    Returns:
        bool: True if access is allowed

    Raises:
        HTTPException: If access is denied
    """
    if authenticated_user["id"] == user_id:
        return True

    raise HTTPException(
        status_code=403,
        detail="You don't have permission to access this resource"
    )

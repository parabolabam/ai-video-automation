#!/usr/bin/env python3
"""
Create an authenticated YouTube Data API service
"""

import logging
import os
from typing import Optional, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from features.youtube.youtube_scopes import youtube_scopes


def _build_service_from_env() -> Optional[Any]:
    logger = logging.getLogger(__name__)
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    if not (client_id and client_secret and refresh_token):
        return None

    try:
        creds: Any = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=youtube_scopes(),
        )
        creds.refresh(Request())
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Env-based YouTube auth failed: {e}")
        return None


def get_youtube_service() -> Optional[Any]:
    logger = logging.getLogger(__name__)

    service = _build_service_from_env()
    if service is not None:
        logger.info("YouTube service initialized via environment credentials")
        return service

    token_file = 'youtube_token.json'
    credentials_file = 'youtube_credentials.json'

    creds: Any | None = None

    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, youtube_scopes())
        except Exception as e:
            logger.warning(f"Failed to load existing token file: {e}")
            creds = None

    if not creds or not getattr(creds, "valid", False):
        if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
                creds = None
        else:
            if not os.path.exists(credentials_file):
                logger.warning("YouTube credentials file not found and no env creds. YouTube upload will be disabled.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, youtube_scopes())
            creds = flow.run_local_server(port=0)
        if creds is not None:
            try:
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.warning(f"Failed to write token file: {e}")

    try:
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Failed to build YouTube service: {e}")
        return None

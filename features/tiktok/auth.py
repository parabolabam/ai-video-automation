#!/usr/bin/env python3
"""
TikTok OAuth helpers (Auth URL, code exchange, refresh) with PKCE
"""

import os
import urllib.parse
import hashlib
import base64
import secrets
from typing import Optional, Dict, Any, Tuple
import httpx


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def generate_pkce_pair(length: int = 64) -> Tuple[str, str]:
    """Return (code_verifier, code_challenge) using S256."""
    verifier = _b64url(secrets.token_bytes(length))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def build_auth_url(client_key: str, redirect_uri: str, state: str = "state123", code_challenge: Optional[str] = None) -> str:
    """Build TikTok auth URL. If code_challenge provided, uses PKCE S256."""
    scope = os.getenv("TIKTOK_SCOPE", "video.upload")
    base = "https://www.tiktok.com/v2/auth/authorize/"
    params = {
        "client_key": client_key,
        "response_type": "code",
        "scope": scope,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"
    q = urllib.parse.urlencode(params)
    return f"{base}?{q}"


def build_auth_url_pkce(client_key: str, redirect_uri: str, state: str = "state123") -> Tuple[str, str]:
    """Return (auth_url, code_verifier) for PKCE flow."""
    verifier, challenge = generate_pkce_pair()
    return build_auth_url(client_key, redirect_uri, state, challenge), verifier


async def exchange_code_for_token(client_key: str, client_secret: str, code: str, redirect_uri: str, code_verifier: Optional[str] = None) -> Optional[Dict[str, Any]]:
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    data: Dict[str, Any] = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    if code_verifier:
        data["code_verifier"] = code_verifier
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, data=data)
        if r.status_code != 200:
            return None
        return r.json()


async def refresh_access_token(client_key: str, client_secret: str, refresh_token: str) -> Optional[Dict[str, Any]]:
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, data=data)
        if r.status_code != 200:
            return None
        return r.json()

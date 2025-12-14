#!/usr/bin/env python3
"""
Web search and research tools for science agents.

Uses DuckDuckGo HTML scraping as the Instant Answer API has rate limits.
"""

import logging
import re
from typing import List

import httpx

logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Raised when a search operation fails."""
    pass


async def search_web_duckduckgo(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo.
    
    Uses the HTML endpoint which is more reliable than the JSON API.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        Formatted search results as a string
        
    Raises:
        SearchError: If the search fails
    """
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            # Use DuckDuckGo HTML lite endpoint
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            if response.status_code != 200:
                raise SearchError(f"DuckDuckGo returned status {response.status_code}")
            
            html = response.text
            
            # Extract results from HTML (simple regex extraction)
            results = []
            
            # Find result snippets
            snippets = re.findall(r'class="result__snippet"[^>]*>([^<]+)<', html)
            titles = re.findall(r'class="result__a"[^>]*>([^<]+)<', html)
            
            for i, (title, snippet) in enumerate(zip(titles[:max_results], snippets[:max_results])):
                title = title.strip()
                snippet = snippet.strip()
                if title and snippet:
                    results.append(f"**{title}**: {snippet}")
            
            if not results:
                # Fallback: try to extract any text content
                text_content = re.sub(r'<[^>]+>', ' ', html)
                text_content = re.sub(r'\s+', ' ', text_content)[:500]
                if "No results" in text_content or not text_content.strip():
                    raise SearchError(f"No search results found for: {query}")
                results.append(f"Search summary: {text_content[:300]}...")
            
            return "\n".join(results)
            
    except httpx.TimeoutException:
        raise SearchError(f"Search timed out for query: {query}")
    except httpx.RequestError as e:
        raise SearchError(f"Search request failed: {e}")
    except Exception as e:
        if isinstance(e, SearchError):
            raise
        raise SearchError(f"Search failed: {e}")


async def search_science_news(topic: str, days: int = 30) -> str:
    """Search for recent science news and discoveries.
    
    Args:
        topic: Science topic to search for
        days: How recent the news should be (for query context)
        
    Returns:
        Formatted news results as a string
        
    Raises:
        SearchError: If the search fails
    """
    enhanced_query = f"{topic} science discovery research news"
    return await search_web_duckduckgo(enhanced_query, max_results=8)


async def verify_science_fact(claim: str) -> str:
    """Attempt to verify a science claim using web search.
    
    Args:
        claim: The science claim to verify
        
    Returns:
        Verification results and sources
        
    Raises:
        SearchError: If the search fails
    """
    query = f"is it true that {claim} science fact"
    return await search_web_duckduckgo(query, max_results=5)

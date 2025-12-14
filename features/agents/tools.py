#!/usr/bin/env python3
"""
Web search and research tools for science agents.

Uses duckduckgo-search library (v8) for reliable searching regarding science facts.
"""

import logging
from typing import List

from ddgs import DDGS

logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Raised when a search operation fails."""
    pass


async def search_web_duckduckgo(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo (Sync wrapped in Async).
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        Formatted search results as a string
    """
    try:
        results = []
        # v8 uses sync context manager
        with DDGS() as ddgs:
            search_results = ddgs.text(query, max_results=max_results)
            
            if not search_results:
                raise SearchError(f"No results found for {query}")
                
            for res in search_results:
                title = res.get("title", "")
                snippet = res.get("body", "")
                link = res.get("href", "")
                if title and snippet:
                    results.append(f"**{title}** ({link}): {snippet}")
                    
        return "\n\n".join(results)
            
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        # Improve error message for known rate limits
        msg = str(e)
        if "202" in msg or "Ratelimit" in msg:
            raise SearchError("DuckDuckGo rate limit or bot detection active.")
        raise SearchError(f"Search failed: {e}")


async def search_science_news(topic: str, days: int = 30) -> str:
    """Search for recent science news and discoveries.
    
    Args:
        topic: Science topic to search for
        days: How recent the news should be (for query context)
        
    Returns:
        Formatted news results as a string
    """
    enhanced_query = f"{topic} science discovery"
    try:
        results = []
        with DDGS() as ddgs:
            # news() is also sync in v8
            news_gen = ddgs.news(enhanced_query, max_results=8)
            
            # Check if news_gen is empty (it might be a list or generator)
            # If generator, we can iterate. 
            # Safest is to list() it if possible, or just iterate.
            
            # We try to iterate.
            found_any = False
            for res in news_gen:
                found_any = True
                title = res.get("title", "")
                snippet = res.get("body", "")
                date = res.get("date", "")
                source = res.get("source", "")
                if title:
                    results.append(f"[{date}] **{title}** ({source}): {snippet}")
            
            if not found_any:
                # Fallback to web search
                 pass

        if not results:
             return await search_web_duckduckgo(enhanced_query + " news", max_results=5)

        return "\n\n".join(results)
    except Exception as e:
        logger.warning(f"News search failed, falling back to web: {e}")
        return await search_web_duckduckgo(enhanced_query + " news", max_results=5)


async def verify_science_fact(claim: str) -> str:
    """Attempt to verify a science claim using web search.
    
    Args:
        claim: The science claim to verify
        
    Returns:
        Verification results and sources
    """
    query = f"is it true that {claim} science fact verify"
    return await search_web_duckduckgo(query, max_results=5)

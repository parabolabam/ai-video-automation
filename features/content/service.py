import logging
import os
from typing import Any, Dict, Optional, Union

from features.openai.gen_prompt import generate_creative_prompt, generate_trending_hashtags

logger = logging.getLogger(__name__)

class ContentService:
    """Service for generating content (prompts, scripts, metadata)."""
    
    def __init__(self, openai_client: Any):
        self.openai_client = openai_client
        
    async def generate_content(self) -> Dict[str, Any]:
        """Generate the core content: prompt, script, and scene plan.
        
        Returns:
            Dict containing:
                - prompt: The visual prompt or base concept
                - voiceover_script: The script for TTS (optional)
                - scenes: List of scene prompts for multi-scene video (optional)
                - total_duration: Estimated duration (optional)
        """
        prompt_result = await generate_creative_prompt(self.openai_client)
        
        content = {
            "prompt": "",
            "voiceover_script": None,
            "scenes": [],
        }
        
        if isinstance(prompt_result, dict):
            if "scenes" in prompt_result:
                # Extended mode - multi-scene
                scenes = prompt_result.get("scenes", [])
                content["scenes"] = scenes
                content["voiceover_script"] = prompt_result.get("voiceover_script", "")
                content["sources"] = prompt_result.get("sources", [])
                content["prompt"] = scenes[0] if scenes else ""
                logger.info(f"Content generated (Extended): {len(scenes)} scenes")
            else:
                # Single scene agent pipeline
                content["prompt"] = prompt_result.get("prompt", "")
                content["voiceover_script"] = prompt_result.get("voiceover_script", "")
                content["sources"] = prompt_result.get("sources", [])
                logger.info("Content generated (Agent Pipeline)")
        else:
            # Direct prompt generation
            content["prompt"] = str(prompt_result)
            logger.info("Content generated (Direct Prompt)")
            
        return content

    async def generate_metadata(self, base_text: str, platform: Optional[str] = None) -> str:
        """Generate trending hashtags and assemble post text."""
        explicit_text = os.getenv("BLOTATO_POST_TEXT")
        text_body = explicit_text or base_text
        
        # Hashtag generation logic
        override = os.getenv("BLOTATO_HASHTAGS")
        if override:
            tags = [f"#{t.strip().lstrip('#')}" for t in override.split(",") if t.strip()]
            tag_string = " ".join(dict.fromkeys(tags))[:200]
        else:
            try:
                plat = (platform or os.getenv("DEFAULT_PLATFORM") or "tiktok").lower()
                tags = await generate_trending_hashtags(self.openai_client, plat, text_body)
                tags = [f"#{t}" for t in tags]
                tag_string = " ".join(dict.fromkeys(tags))[:200]
            except Exception:
                # Fallback logic
                defaults = ["ai", "viral", "shorts"]
                words = [w.strip().lower() for w in text_body.replace("\n", " ").split(" ") if len(w) >= 4][:5]
                words = ["".join(ch for ch in w if ch.isalnum()) for w in words]
                uniq = []
                for w in words + defaults:
                    tag = f"#{w}"
                    if w and tag not in uniq:
                        uniq.append(tag)
                tag_string = " ".join(uniq)[:200]
                
        return f"{text_body}\n\n{tag_string}".strip()

    async def generate_search_tags(self, context_text: str, platform: Optional[str] = None) -> str:
        """Generate only the hashtag string for a given context."""
        override = os.getenv("BLOTATO_HASHTAGS")
        if override:
            tags = [f"#{t.strip().lstrip('#')}" for t in override.split(",") if t.strip()]
            tag_string = " ".join(dict.fromkeys(tags))[:200]
        else:
            try:
                plat = (platform or os.getenv("DEFAULT_PLATFORM") or "tiktok").lower()
                tags = await generate_trending_hashtags(self.openai_client, plat, context_text)
                tags = [f"#{t}" for t in tags]
                tag_string = " ".join(dict.fromkeys(tags))[:200]
            except Exception:
                # Fallback logic
                defaults = ["ai", "viral", "shorts"]
                words = [w.strip().lower() for w in context_text.replace("\n", " ").split(" ") if len(w) >= 4][:5]
                words = ["".join(ch for ch in w if ch.isalnum()) for w in words]
                uniq = []
                for w in words + defaults:
                    tag = f"#{w}"
                    if w and tag not in uniq:
                        uniq.append(tag)
                tag_string = " ".join(uniq)[:200]
        return tag_string

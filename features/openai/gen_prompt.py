#!/usr/bin/env python3
"""
Generate creative video prompt using multi-agent research pipeline.

Uses a three-agent system:
1. Researcher - Finds interesting science facts
2. Evaluator - Validates accuracy
3. Audience Analyst - Selects the most viral-worthy fact

Then generates a video description using the selected fact.
"""

import logging
import os
from datetime import datetime
from typing import Any, List

from features.openai.conversation_state import (
    load_previous_response_id,
    save_response_id,
)

logger = logging.getLogger(__name__)


async def generate_creative_prompt(openai_client: Any) -> str | dict[str, Any]:
    """Generate a creative video prompt using multi-agent research or direct generation.
    
    Modes:
    - EXTENDED_MODE=true: Multi-scene pipeline (4 scenes, 32s video)
    - USE_AGENT_PIPELINE=true: Single-scene agent pipeline (8s video)
    - Neither: Direct OpenAI generation (8s video)
    
    Returns:
        str: Video prompt (if direct generation)
        dict: {'prompt': str, 'voiceover_script': str} (single scene)
        dict: {'scenes': list, 'voiceover_script': str, ...} (extended mode)
    """
    extended_mode = os.getenv("EXTENDED_MODE", "false").lower() == "true"
    use_agents = os.getenv("USE_AGENT_PIPELINE", "false").lower() == "true"
    
    if extended_mode:
        return await _generate_extended(openai_client)
    elif use_agents:
        return await _generate_with_agents(openai_client)
    else:
        return await _generate_direct(openai_client)


async def _generate_extended(openai_client: Any) -> dict[str, Any]:
    """Generate multi-scene video content using extended pipeline.
    
    Returns:
        Dict with 'scenes', 'voiceover_script', 'fact', etc.
    """
    num_scenes = int(os.getenv("VIDEO_SCENES", "4"))
    
    logger.info(f"Starting extended multi-scene pipeline ({num_scenes} scenes)...")
    
    from features.agents.science_agents import run_extended_pipeline
    
    result = await run_extended_pipeline(num_scenes)
    
    logger.info(f"Extended pipeline generated {len(result.get('scenes', []))} scenes")
    return result


async def _generate_with_agents(openai_client: Any) -> dict[str, str]:
    """Generate prompt using the multi-agent research pipeline.
    
    Returns:
        Dict with 'prompt' and 'voiceover_script' keys
        
    Raises:
        RuntimeError: If the agent pipeline fails
    """
    logger.info("Starting multi-agent science research pipeline...")
    
    from features.agents.science_agents import run_science_research_pipeline
    
    # Run the full pipeline - let exceptions propagate
    result = await run_science_research_pipeline()
    
    fact = result.get("fact", "")
    visual = result.get("visual_concept", "")
    voiceover_script = result.get("voiceover_script", "")
    
    if not fact:
        raise RuntimeError("Agent pipeline returned empty fact")
    
    # Combine into a video description
    if visual:
        prompt = f"{visual} {fact}"
    else:
        prompt = fact
        
    logger.info(f"Agent pipeline generated: {prompt[:200]}...")
    
    return {
        "prompt": prompt,
        "voiceover_script": voiceover_script,
        "sources": result.get("sources", [])
    }


async def _generate_direct(openai_client: Any) -> str:
    """Generate prompt using direct OpenAI Responses API with conversation continuity."""
    try:
        logger.info("Generating creative prompt with OpenAI Responses API...")

        # Load previous response ID for conversation continuity
        previous_response_id = load_previous_response_id()
        if previous_response_id:
            logger.info(f"Continuing conversation from response: {previous_response_id[:20]}...")
        else:
            logger.info("Starting new conversation (no previous response ID)")

        system_prompt = """You are a creative director for viral short-form science content. Generate concise, vivid video descriptions that visualize amazing science facts.

CRITICAL: You have been generating video descriptions in previous messages. You MUST create something COMPLETELY DIFFERENT from anything you've generated before. Never repeat topics, subjects, or similar scientific concepts.

Guidelines:
- Choose a mind-blowing science fact and visualize it
- Describe a HYPER-REALISTIC, CINEMATIC 8-second scene (Think IMAX Documentary)
- Focus on ONE clear scientific concept
- Be specific about visuals, movement, and mood
- Keep it concise (2-3 sentences max)
- STYLE: Photorealistic, 8k, highly detailed, dramatic lighting. NO CGI/CARTOON looks.

Good examples:
- "A photorealistic close-up of a neutron star spinning 700 times per second, accurately rendering the magnetic field ripping glowing plasma streams in a documentary style."
- "Inside a human cell, captured with a macro lens, organelles move with organic imperfection and texture—not a smooth 3D render, but a biological reality."
- "A bullet fired through a soap bubble, filmed with a high-speed Phantom Flex camera, showing liquid surface tension tearing with crystal clarity."

Output ONLY the science-focused video description, nothing else."""

        user_prompt = (
            f"Generate a unique video description for today ({datetime.now().strftime('%Y-%m-%d')}). "
            f"Make it visually stunning and DIFFERENT from all previous descriptions in our conversation."
        )

        # Use Responses API with previous_response_id for stateful conversation
        response_params = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
            "instructions": system_prompt,
            "input": user_prompt,
            "max_output_tokens": 4600,
            "temperature": 0.8,
        }
        
        # Add previous response ID if available for conversation continuity
        if previous_response_id:
            response_params["previous_response_id"] = previous_response_id

        response = await openai_client.responses.create(**response_params)

        # Extract the generated text from the response
        prompt = response.output_text.strip()
        logger.info(f"Generated prompt: {prompt[:200]}...")

        # Save response ID for next run
        save_response_id(response.id)
        logger.info(f"Saved response ID for conversation continuity: {response.id[:20]}...")

        return prompt

    except Exception as e:
        logger.error(f"Failed to generate prompt with OpenAI: {e}")
        fallback_prompts = [
            "A mesmerizing timelapse of clouds forming and dissolving over a mountain range at sunset",
            "Abstract flowing liquid metal with rainbow reflections in slow motion",
            "A futuristic city with flying cars and neon lights, cinematic view",
            "Underwater scene with bioluminescent jellyfish dancing in the deep ocean",
            "Close-up of colorful paint drops falling into water in super slow motion"
        ]
        import random
        return random.choice(fallback_prompts)


async def generate_trending_hashtags(
    openai_client: Any, platform: str, topic: str
) -> List[str]:
    """Return a list of trending-style hashtags for a given platform and topic.

    Output is a small list (5-12) of concise, high-signal tags without the leading '#'.
    """
    try:
        system = (
            "You are a social media growth strategist who crafts concise, high-signal hashtags. "
            "Return only a comma-separated list of 5-12 platform-appropriate hashtags, no explanations. "
            "Do not include the leading '#'. Avoid banned or misleading tags."
        )
        user = (
            f"Platform: {platform}. Topic: {topic[:300]}. "
            "Optimize for discovery and high intent."
        )
        resp = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        text = resp.choices[0].message.content.strip()
        # Parse comma-separated list, sanitize
        parts = [p.strip() for p in text.split(",") if p.strip()]
        cleaned: List[str] = []
        for p in parts:
            tag = p.lstrip("#").replace(" ", "").lower()
            tag = "".join(ch for ch in tag if ch.isalnum())
            if tag and tag not in cleaned:
                cleaned.append(tag)
        # Clamp length
        return cleaned[:12]
    except Exception as e:
        logger.warning(f"Falling back to basic hashtags: {e}")
        return ["ai", "viral", "shorts", "trend", "discover"]

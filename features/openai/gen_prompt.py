#!/usr/bin/env python3
"""
Generate creative video prompt using OpenAI
"""

import logging
from datetime import datetime
from typing import Any


async def generate_creative_prompt(openai_client: Any) -> str:
    """Generate a creative video prompt using OpenAI."""
    logger = logging.getLogger(__name__)
    try:
        logger.info("Generating creative prompt with OpenAI...")

        system_prompt = (
            "You are a creative video content generator. Generate a single, engaging video prompt "
            "for a short vertical video (under 60 seconds) that would work well for YouTube Shorts.\n\n"
            "The prompt should be:\n"
            "- Visually interesting and dynamic\n"
            "- Suitable for vertical video format\n"
            "- Engaging for social media audience\n"
            "- Clear and specific enough for AI video generation\n"
            "- Original and creative\n\n"
            "Focus on topics like: nature, abstract art, futuristic concepts, satisfying visuals, or trending themes.\n\n"
            "Return ONLY the video prompt, nothing else."
        )

        user_prompt = (
            f"Generate a creative video prompt for today ({datetime.now().strftime('%Y-%m-%d')}). "
            f"Make it unique and engaging."
        )

        response = await openai_client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4600,
            temperature=0.8
        )

        prompt = response.choices[0].message.content.strip()
        logger.info(f"Generated prompt: {prompt}")
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

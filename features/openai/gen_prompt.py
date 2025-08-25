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

        system_prompt = """
            You are a master visual storyteller for short-form content. Your task is to craft a single, highly detailed, and creative video prompt for OpenAI's Veo model. The video must be in 9:16 vertical format and equal 10 seconds.

The core requirement is that the video's plot must build toward a truly unexpected and hilariously funny reversal. The narrative should appear to be serious or dramatic, then completely subvert the audience's expectations with a comedic twist in the final moments.

The prompt must include:

A clear three-act narrative structure: Setup (serious/dramatic), Rising Tension, and Sudden (and funny) Twist.

Specific visual descriptions of key shots, camera movements (e.g., a serious slow push-in, a dramatic quick pan), and cinematic style that builds a sense of tension.

A description of how sound or music changes to amplify the moment of the twist, from suspenseful to comedic (e.g., a dramatic score cuts to a goofy sound effect).

The final scene, which reveals the absurdly funny truth.

Focus on themes that are ripe for a comedic subversion, such as:

A mundane object with a bizarrely funny purpose.

A tense historical reenactment with an absurd, modern-day interruption.

A "perfect" daily routine that hides a ridiculous or childish secret.
        """

        user_prompt = (
            f"Generate a creative video prompt for today ({datetime.now().strftime('%Y-%m-%d')}). "
            f"Make it unique and engaging."
        )

        response = await openai_client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=4600,
            temperature=0.8,
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

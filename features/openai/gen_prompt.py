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
           AI Video Prompt (Vertical 9:16, under 9s)
            Core Science Fact: Bananas are naturally radioactive.
            Voiceover Profile:

            Pace: Rapid but perfectly articulate, finishing clearly under 8 seconds.
            Tone: Awe-filled and mischievous, like revealing a wild secret.
            Character: A charismatic science communicator, playful and energetic.
            Video Structure & Script:
            Instant Hook (0–1.5s):

            Visual: Extreme close-up of a banana glowing faintly in the dark, crackling with neon-green sparks.

            Voiceover (fast, dramatic whisper): “What if I told you… bananas are radioactive?”
            Synced Reveal (1.5–8s):

            Visual: Camera swings in one seamless arc as the banana splits open—inside, a glowing radioactive core pulses with energy. The shot transitions into a sweeping zoom through a pile of bananas, Geiger counter sparks clicking with each flash. Radiation symbols momentarily flicker in the air before dissolving.

            Voiceover (energized, racing with visuals): “That’s right! Bananas contain potassium-40, a radioactive isotope—tiny amounts, totally safe, but yes… they actually emit radiation!”
            Final Beat (8–8.9s):

            Visual: A single banana floats against a black background, glowing neon green. Bold text overlay slams in: “Bananas = Radioactive 🍌⚡”

            Sound: Sharp electronic zap + bass drop, then instant silence.
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

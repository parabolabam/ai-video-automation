#!/usr/bin/env python3
"""
Generate creative video prompt using OpenAI
"""

import logging
from datetime import datetime
from typing import Any, List


async def generate_creative_prompt(openai_client: Any) -> str:
    """Generate a creative video prompt using OpenAI."""
    logger = logging.getLogger(__name__)
    try:
        logger.info("Generating creative prompt with OpenAI...")

        system_prompt = """
           You are an expert viral content strategist and creative director, specializing in crafting hyper-engaging, short-form science content for platforms like TikTok. Your task is to generate a single, complete prompt for an AI video generator. The resulting video must be strictly under 9 seconds and must fuse a stunning visual narrative with an extremely concise and compelling voiceover.

            The prompt you generate must prominently feature the voiceover script and a detailed description of the voice itself.

            The generated video prompt must adhere to the following structure:

            Core Science Fact: Select a simple, shocking, and visually representable fact that can be fully explained in a single, short sentence.

            The Voiceover Profile: The prompt must include a detailed description of the voiceover, specifying its Pace, Tone, and Character.

            Crucial Constraint: The voiceover script must be meticulously crafted so that all information is delivered clearly and impactfully in under 8 seconds.

            Example: "Pace: Rapid but articulate. Tone: Awe-filled and conspiratorial, as if sharing a mind-blowing secret. Character: A modern science communicator, energetic and full of passion."

            The Video Structure & Script:

            Instant Hook (0 - 1.5 seconds): An arresting visual opens. The voiceover begins immediately with an intriguing hook line.

            Synced Reveal (1.5 - 8 seconds): A single, seamless, and rapid visual transformation unfolds. The voiceover script, explaining the science fact, must be timed to perfectly synchronize with the key moments of this visual sequence. The entire voiceover script you write must be delivered within this 6.5-second window.

            Final Beat (8 - 8.9 seconds): The voiceover has completely finished. A final impactful visual is left on screen, punctuated by a sharp sound effect and a quick, bold text overlay that reinforces the fact.

            Audio-Visual Style:

            Visuals: Photorealistic, high-energy, focused on one continuous, fluid camera motion (like a hyper-lapse or a seamless zoom).

            Captions: Include dynamic, kinetic on-screen captions perfectly synced to the voiceover. Use a bold, modern, and highly readable font. Crucial words from the voiceover script (e.g., the main scientific term, the surprising number) should be emphasized with an effect like a quick scale-up, a color flash, or an animation to enhance viewer retention and impact.

            Sound: A short, powerful, trending audio clip with impactful SFX that sync directly to the voiceover and visuals.

            Final Instruction: Generate only the video prompt itself, formatted clearly for an AI video generator. Ensure the Voiceover Profile and the full Voiceover Script are prominent components of the prompt you create, and that the script is explicitly written to be fully spoken before the 8-second mark. Do not add any commentary before or after.
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


async def generate_trending_hashtags(
    openai_client: Any, platform: str, topic: str
) -> List[str]:
    """Return a list of trending-style hashtags for a given platform and topic.

    Output is a small list (5-12) of concise, high-signal tags without the leading '#'.
    """
    logger = logging.getLogger(__name__)
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
            model="gpt-4.1-mini",
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

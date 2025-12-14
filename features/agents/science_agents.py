#!/usr/bin/env python3
"""
Multi-agent science research system using OpenAI Agents SDK.

Three agents work together:
1. Researcher - Finds interesting science facts
2. Evaluator - Validates accuracy and filters unreliable claims
3. Audience Analyst - Scores viral potential and selects the best fact
"""

import logging
from typing import Any

from agents import Agent, Runner, function_tool

from features.agents.tools import search_web_duckduckgo, search_science_news, verify_science_fact

logger = logging.getLogger(__name__)


# Define tools as function_tools for the agents
@function_tool
async def web_search(query: str) -> str:
    """Search the web for information about a topic.
    
    Args:
        query: The search query to look up
        
    Returns:
        Search results as formatted text
    """
    return await search_web_duckduckgo(query, max_results=5)


@function_tool
async def science_news_search(topic: str) -> str:
    """Search for recent science news and discoveries.
    
    Args:
        topic: The science topic to search for
        
    Returns:
        Recent news and discoveries about the topic
    """
    return await search_science_news(topic, days=30)


@function_tool
async def fact_check(claim: str) -> str:
    """Verify a science claim by searching for corroborating sources.
    
    Args:
        claim: The science claim to verify
        
    Returns:
        Verification results and sources
    """
    return await verify_science_fact(claim)


# Global storage for scene plan (captured via tool call)
_scene_plan_result: dict = {}


@function_tool
def submit_scene_plan(style_keywords: str, scenes: list[str]) -> str:
    """Submit the scene plan with structured data – MUST be called to complete the task.
    
    Args:
        style_keywords: 5 comma-separated style keywords (e.g. "cinematic, photorealistic, 8K, documentary, macro")
        scenes: List of visual descriptions for each 8-second scene. The number of scenes must match the requested count.
        
    Returns:
        Confirmation message
    """
    global _scene_plan_result
    _scene_plan_result = {
        "style_keywords": style_keywords,
        "scenes": scenes
    }
    return f"Scene plan submitted successfully with {len(scenes)} scenes."


def get_scene_plan_result() -> dict:
    """Get the scene plan result captured from the tool call."""
    global _scene_plan_result
    return _scene_plan_result


def clear_scene_plan_result() -> None:
    """Clear the scene plan result."""
    global _scene_plan_result
    _scene_plan_result = {}


# Define the three agents
def create_researcher_agent() -> Agent:
    """Create the Science Researcher agent."""
    return Agent(
        name="ScienceResearcher",
        model="gpt-4o",
        instructions="""You are a science researcher specializing in finding fascinating, mind-blowing science facts.

Your task is to find 5 interesting science facts that would make great short-form video content.

Guidelines:
- Look for facts that are visually representable
- Focus on topics like: space, physics, biology, chemistry, nature, technology
- Include both recent discoveries and timeless amazing facts
- Each fact should be simple enough to explain in 8 seconds
- Avoid controversial or unverified claims

Use the web_search and science_news_search tools to find facts.

Output format: List exactly 5 facts, each on its own line, with a brief explanation.
Example:
1. [FACT]: Neutron stars spin up to 700 times per second. [WHY INTERESTING]: This is faster than a kitchen blender.
2. [FACT]: Honey never spoils. [WHY INTERESTING]: 3000-year-old honey from Egyptian tombs is still edible.
...
""",
        tools=[web_search, science_news_search],
    )


def create_evaluator_agent() -> Agent:
    """Create the Fact Evaluator agent."""
    return Agent(
        name="FactEvaluator",
        model="gpt-4o",
        instructions="""You are a science fact-checker and evaluator.

Your task is to evaluate the science facts provided and filter out any that are:
- Inaccurate or misleading
- Exaggerated beyond the truth
- Not verifiable from reliable sources
- Too complex to visualize

Use the fact_check tool to verify claims you're unsure about.

For each valid fact, rate its:
- Accuracy (1-10): How scientifically accurate is this claim?
- Visualizability (1-10): How easy would this be to show in an 8-second video?
- Wow Factor (1-10): How surprising/interesting is this to the average person?

Output format: List the validated facts with their scores.
Only include facts that score at least 7 on accuracy.
""",
        tools=[fact_check, web_search],
    )


def create_audience_analyst_agent() -> Agent:
    """Create the Audience Analyst agent."""
    return Agent(
        name="AudienceAnalyst",
        model="gpt-4o",
        instructions="""You are a viral content strategist specializing in short-form science content.

Your task is to analyze the validated science facts and select THE SINGLE BEST ONE for a viral TikTok/YouTube Shorts video.

Consider:
- Viral potential: Would this make people share it?
- Visual appeal: Can this be shown in a stunning 8-second video?
- Hook strength: Does this have a "wait, what?!" factor?
- Broad appeal: Would this interest people outside science enthusiasts?

Output ONLY the winning fact in this exact format:

SELECTED_FACT: [The science fact as a single clear sentence]
VISUAL_CONCEPT: [Brief 1-2 sentence description of how to visualize this]
HOOK: [A compelling 5-word hook to start the video]
""",
        tools=[],
    )

def create_script_writer_agent(duration_seconds: int = 8) -> Agent:
    """Create the Script Writer agent for voiceover narration.
    
    Args:
        duration_seconds: Target duration for the voiceover
    """
    # Calculate word count based on duration (approx 2.5-3 words per second)
    word_count_min = int(duration_seconds * 2.5)
    word_count_max = int(duration_seconds * 3)
    
    return Agent(
        name="ScriptWriter",
        model="gpt-4o",
        instructions=f"""You are a professional voiceover artist writing scripts that sound COMPLETELY NATURAL and HUMAN.

Write a voiceover script for a {duration_seconds}-second science video that sounds like a REAL PERSON talking to a friend - NOT like AI or a robot.

CRITICAL FOR NATURAL SPEECH:
- Write like you SPEAK, not like you write
- Use contractions (don't, can't, it's, there's)
- Include natural filler transitions ("Now,", "See,", "Here's the thing:")
- Vary sentence length - mix short punchy with longer flowing
- Add rhetorical questions to create engagement
- Use everyday vocabulary, avoid jargon
- Include emotional reactions ("Crazy, right?", "Mind-blowing!", "Wild.")

PACING for {duration_seconds} seconds:
- Word count: {word_count_min}-{word_count_max} words
- Start with an attention-grabbing hook (2-3s)
- Build naturally through the explanation
- End with an impactful closer

DO NOT:
- Sound robotic or overly formal
- Use AI-typical phrases like "In conclusion" or "It's worth noting"
- Be monotonous - vary the emotional energy
- Use too many [Pause] markers - just 1-2 max
- NEVER include "Scene 1", "Scene 2", or any metadata labels
- NEVER mention scenes, sections, or timestamps in the spoken text
- Output ONLY what should be SPOKEN aloud - no headers or labels

Output ONLY in this format:

VOICEOVER_SCRIPT: [Natural, conversational script that sounds human, {word_count_min}-{word_count_max} words - NO scene labels or metadata]
""",
        tools=[],
    )


def create_scene_planner_agent(num_scenes: int = 4) -> Agent:
    """Create the Scene Planner agent for multi-scene videos.
    
    Args:
        num_scenes: Number of scenes to generate (default 4 for ~32s video)
    """
    return Agent(
        name="ScenePlanner",
        model="gpt-4o",
        instructions=f"""You are a Hollywood cinematographer creating HYPER-REALISTIC science videos.

Your task is to break down a science fact into {num_scenes} distinct visual scenes.
Each scene will be 8 seconds long, for a total of {num_scenes * 8} seconds.

CRITICAL REQUIREMENTS FOR PHOTOREALISM:
- ALL scenes must look like REAL footage, NOT AI-generated
- Use REAL-WORLD reference (documentary, nature films, NASA footage style)
- Describe REAL lighting conditions (golden hour, overcast, studio lighting)
- Include NATURAL imperfections (lens flares, shallow depth of field, motion blur)
- Specify REAL camera equipment style (ARRI Alexa, RED camera, macro lens, drone footage)
- Avoid fantasy, abstract, or obviously CGI descriptions

VISUAL CONSISTENCY across all scenes:
- Same color grading (cinematic, desaturated, warm tones, etc.)
- Same camera style (handheld, steadicam, locked tripod, etc.)
- Same aspect ratio feel (anamorphic, widescreen)
- Seamless flow between scenes

Scene structure:
- Scene 1: HOOK - Dramatic real-world opening shot
- Scene 2-{num_scenes-1}: JOURNEY - Documentary-style exploration
- Scene {num_scenes}: PAYOFF - Stunning conclusion

For EACH scene include:
1. Specific real-world location or setting
2. Exact lighting description
3. Camera movement and lens type
4. Natural environmental details

Important: You MUST call the submit_scene_plan tool with your scenes to complete the task.
Pass the scenes as a LIST of strings, e.g. ["Scene 1 description...", "Scene 2 description..."].
Do not output text - call the tool with the structured arguments.""",
        tools=[submit_scene_plan],
    )


async def run_science_research_pipeline() -> dict[str, str]:
    """Run the full multi-agent science research pipeline.
    
    Returns:
        Dictionary with 'fact', 'visual_concept', 'hook', and 'voiceover_script' keys
        
    Raises:
        Exception: If any step in the pipeline fails
    """
    logger.info("Starting multi-agent science research pipeline...")
    
    # Create agents
    researcher = create_researcher_agent()
    evaluator = create_evaluator_agent()
    analyst = create_audience_analyst_agent()
    script_writer = create_script_writer_agent()
    
    # Create runner
    runner = Runner()
    
    # Step 1: Research science facts
    logger.info("Agent 1 (Researcher): Finding science facts...")
    try:
        research_result = await runner.run(
            researcher,
            "Find 5 mind-blowing science facts that would make great viral video content. Use web search to find real, verified facts."
        )
        facts = research_result.final_output
        if not facts or len(facts) < 50:
            raise ValueError(f"Researcher returned insufficient output: {facts}")
        logger.info(f"Researcher found facts: {facts[:200]}...")
    except Exception as e:
        logger.error(f"Researcher agent failed: {e}")
        raise RuntimeError(f"Pipeline step 1 (Researcher) failed: {e}") from e
    
    # Step 2: Evaluate and validate facts
    logger.info("Agent 2 (Evaluator): Validating facts...")
    try:
        eval_result = await runner.run(
            evaluator,
            f"Evaluate these science facts for accuracy and visual potential:\n\n{facts}"
        )
        validated_facts = eval_result.final_output
        if not validated_facts or len(validated_facts) < 50:
            raise ValueError(f"Evaluator returned insufficient output: {validated_facts}")
        logger.info(f"Evaluator validated: {validated_facts[:200]}...")
    except Exception as e:
        logger.error(f"Evaluator agent failed: {e}")
        raise RuntimeError(f"Pipeline step 2 (Evaluator) failed: {e}") from e
    
    # Step 3: Select the best fact for viral potential
    logger.info("Agent 3 (Analyst): Selecting best fact for viral content...")
    try:
        analyst_result = await runner.run(
            analyst,
            f"Select the single best science fact for a viral video from these validated facts:\n\n{validated_facts}"
        )
        final_selection = analyst_result.final_output
        if not final_selection:
            raise ValueError("Analyst returned empty output")
        logger.info(f"Analyst selected: {final_selection}")
    except Exception as e:
        logger.error(f"Analyst agent failed: {e}")
        raise RuntimeError(f"Pipeline step 3 (Analyst) failed: {e}") from e
    
    # Parse the analyst output
    result = {
        "fact": "",
        "visual_concept": "",
        "hook": "",
        "voiceover_script": "",
        "raw_output": final_selection
    }
    
    for line in final_selection.split("\n"):
        if line.startswith("SELECTED_FACT:"):
            result["fact"] = line.replace("SELECTED_FACT:", "").strip()
        elif line.startswith("VISUAL_CONCEPT:"):
            result["visual_concept"] = line.replace("VISUAL_CONCEPT:", "").strip()
        elif line.startswith("HOOK:"):
            result["hook"] = line.replace("HOOK:", "").strip()
    
    if not result["fact"]:
        raise ValueError(f"Failed to parse SELECTED_FACT from output: {final_selection[:200]}")
    
    # Step 4: Write voiceover script
    logger.info("Agent 4 (Script Writer): Creating voiceover script...")
    try:
        script_result = await runner.run(
            script_writer,
            f"Write a voiceover script for this science video:\n\nFact: {result['fact']}\nVisual concept: {result['visual_concept']}\nHook phrase: {result['hook']}"
        )
        script_output = script_result.final_output
        if not script_output:
            raise ValueError("Script Writer returned empty output")
        
        # Parse voiceover script
        for line in script_output.split("\n"):
            if line.startswith("VOICEOVER_SCRIPT:"):
                result["voiceover_script"] = line.replace("VOICEOVER_SCRIPT:", "").strip()
        
        if not result["voiceover_script"]:
            # Fallback: use the whole output as script
            result["voiceover_script"] = script_output.strip()
        
        logger.info(f"Script Writer created: {result['voiceover_script']}")
    except Exception as e:
        logger.error(f"Script Writer agent failed: {e}")
        raise RuntimeError(f"Pipeline step 4 (Script Writer) failed: {e}") from e
    
    logger.info(f"Pipeline complete. Selected fact: {result['fact'][:100]}...")
    return result


async def run_extended_pipeline(num_scenes: int = 4) -> dict[str, Any]:
    """Run the extended multi-scene video pipeline.
    
    This pipeline generates multiple scene prompts for a longer video,
    plus a voiceover script timed for the full duration.
    
    Args:
        num_scenes: Number of 8-second scenes (default 4 = 32s video)
        
    Returns:
        Dictionary with:
        - 'fact': The science fact
        - 'scenes': List of scene prompts
        - 'style_keywords': Consistent style keywords
        - 'voiceover_script': Full-length voiceover script
        - 'total_duration': Total video duration in seconds
    """
    total_duration = num_scenes * 8
    logger.info(f"Starting extended pipeline ({num_scenes} scenes, {total_duration}s total)...")
    
    # Create agents
    researcher = create_researcher_agent()
    evaluator = create_evaluator_agent()
    analyst = create_audience_analyst_agent()
    scene_planner = create_scene_planner_agent(num_scenes)
    script_writer = create_script_writer_agent(total_duration)
    
    runner = Runner()
    
    # Steps 1-3: Same as regular pipeline (research, evaluate, select)
    logger.info("Agent 1 (Researcher): Finding science facts...")
    try:
        research_result = await runner.run(
            researcher,
            "Find 5 mind-blowing science facts that would make great viral video content. Use web search to find real, verified facts."
        )
        facts = research_result.final_output
        if not facts or len(facts) < 50:
            raise ValueError(f"Researcher returned insufficient output")
        logger.info(f"Researcher found facts: {facts[:200]}...")
    except Exception as e:
        raise RuntimeError(f"Pipeline step 1 (Researcher) failed: {e}") from e
    
    logger.info("Agent 2 (Evaluator): Validating facts...")
    try:
        eval_result = await runner.run(
            evaluator,
            f"Evaluate these science facts for accuracy and visual potential:\n\n{facts}"
        )
        validated_facts = eval_result.final_output
        logger.info(f"Evaluator validated: {validated_facts[:200]}...")
    except Exception as e:
        raise RuntimeError(f"Pipeline step 2 (Evaluator) failed: {e}") from e
    
    logger.info("Agent 3 (Analyst): Selecting best fact...")
    try:
        analyst_result = await runner.run(
            analyst,
            f"Select the single best science fact for a viral video:\n\n{validated_facts}"
        )
        selection = analyst_result.final_output
        logger.info(f"Analyst selected: {selection[:200]}...")
    except Exception as e:
        raise RuntimeError(f"Pipeline step 3 (Analyst) failed: {e}") from e
    
    # Parse fact
    fact = ""
    for line in selection.split("\n"):
        if line.startswith("SELECTED_FACT:"):
            fact = line.replace("SELECTED_FACT:", "").strip()
    if not fact:
        fact = selection.split("\n")[0]  # Fallback
    
    # Step 4: Plan scenes using structured tool output
    logger.info(f"Agent 4 (Scene Planner): Creating {num_scenes} visual scenes...")
    clear_scene_plan_result()  # Clear any previous result
    try:
        scene_result = await runner.run(
            scene_planner,
            f"Create {num_scenes} visually consistent scenes for this science fact:\n\n{fact}"
        )
        logger.info(f"Scene Planner completed")
    except Exception as e:
        raise RuntimeError(f"Pipeline step 4 (Scene Planner) failed: {e}") from e
    
    # Get structured scene data from tool call
    scene_plan = get_scene_plan_result()
    style_keywords = scene_plan.get("style_keywords", "")
    raw_scenes = scene_plan.get("scenes", [])
    
    # Build scene prompts with style keywords
    scenes = []
    for scene_content in raw_scenes:
        if scene_content:
            if style_keywords:
                scene_prompt = f"{style_keywords}. {scene_content}"
            else:
                scene_prompt = scene_content
            scenes.append(scene_prompt)
    
    logger.info(f"Got {len(scenes)} scenes from structured output")
    
    if len(scenes) < num_scenes:
        logger.warning(f"Only got {len(scenes)} scenes, expected {num_scenes}")
        # Pad with the last scene if needed
        while len(scenes) < num_scenes and scenes:
            scenes.append(scenes[-1])
    
    # Build scene descriptions for script writer
    scene_descriptions = "\n".join([
        f"Scene {i+1} (seconds {i*8}-{(i+1)*8}): {scene}"
        for i, scene in enumerate(scenes)
    ])
    
    # Step 5: Write voiceover script MATCHING the scenes
    logger.info(f"Agent 5 (Script Writer): Creating {total_duration}s voiceover synced to scenes...")
    try:
        script_result = await runner.run(
            script_writer,
            f"""Write a {total_duration}-second voiceover script that EXACTLY MATCHES these visual scenes.

SCIENCE FACT: {fact}

VISUAL SCENES (what viewer sees):
{scene_descriptions}

CRITICAL: Your voiceover must describe and enhance EXACTLY what's shown in each scene at that moment.
- When Scene 1 shows X, your words must talk about X
- When Scene 2 transitions to Y, your words must flow into Y
- Each 8 seconds of voiceover must sync with its corresponding scene

Write the script so audio and video tell the SAME story together."""
        )
        script_output = script_result.final_output
        
        voiceover_script = ""
        for line in script_output.split("\n"):
            if line.startswith("VOICEOVER_SCRIPT:"):
                voiceover_script = line.replace("VOICEOVER_SCRIPT:", "").strip()
        
        if not voiceover_script:
            voiceover_script = script_output.strip()
        
        logger.info(f"Script Writer created: {voiceover_script[:100]}...")
    except Exception as e:
        raise RuntimeError(f"Pipeline step 5 (Script Writer) failed: {e}") from e
    
    result = {
        "fact": fact,
        "scenes": scenes,
        "style_keywords": style_keywords,
        "voiceover_script": voiceover_script,
        "total_duration": total_duration,
        "num_scenes": len(scenes),
    }
    
    logger.info(f"Extended pipeline complete. {len(scenes)} scenes, {total_duration}s total.")
    return result

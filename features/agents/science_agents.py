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

from features.agents.researcher import create_researcher_agent
from features.agents.evaluator import create_evaluator_agent
from features.agents.analyst import create_audience_analyst_agent
from features.agents.script_writer import create_script_writer_agent
from features.agents.scene_planner import (
    create_scene_planner_agent, 
    submit_scene_plan, 
    get_scene_plan_result, 
    clear_scene_plan_result
)

logger = logging.getLogger(__name__)

# NOTE: Functions for creating agents have been moved to their respective files.
# science_agents.py now acts as the pipeline orchestrator.


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
        # Structured output: research_result.final_output is ResearcherOutput
        facts_list = research_result.final_output.facts
        if not facts_list:
            raise ValueError(f"Researcher returned empty list")
        
        # Serialize facts for formatting to next agent
        facts_text = "\n".join([f"{i+1}. [FACT]: {f.fact_text} [WHY INTERESTING]: {f.explanation}" for i, f in enumerate(facts_list)])
        logger.info(f"Researcher found {len(facts_list)} facts.")
    except Exception as e:
        logger.error(f"Researcher agent failed: {e}")
        raise RuntimeError(f"Pipeline step 1 (Researcher) failed: {e}") from e
    
    # Step 2: Evaluate and validate facts
    logger.info("Agent 2 (Evaluator): Validating facts...")
    try:
        eval_result = await runner.run(
            evaluator,
            f"Evaluate these science facts for accuracy and visual potential:\n\n{facts_text}"
        )
        # Structured output: eval_result.final_output is EvaluatorOutput
        validated_facts = eval_result.final_output.validated_facts
        if not validated_facts:
            raise ValueError(f"Evaluator returned empty list")
            
        logger.info(f"Evaluator validated {len(validated_facts)} facts.")
        
        # Serialize for next agent
        validated_text = ""
        for vf in validated_facts:
            validated_text += f"- Fact: {vf.fact_text}\n  Scores: Acc={vf.accuracy_score}, Vis={vf.visualizability_score}, Wow={vf.wow_factor_score}\n  Notes: {vf.explanation}\n"
    except Exception as e:
        logger.error(f"Evaluator agent failed: {e}")
        raise RuntimeError(f"Pipeline step 2 (Evaluator) failed: {e}") from e
    
    # Step 3: Select the best fact for viral potential
    logger.info("Agent 3 (Analyst): Selecting best fact for viral content...")
    try:
        analyst_result = await runner.run(
            analyst,
            f"Select the single best science fact for a viral video from these validated facts:\n\n{validated_text}"
        )
        # Structured output: analyst_result.final_output is ViralContentSelection
        selection = analyst_result.final_output
        logger.info(f"Analyst selected: {selection.selected_fact}")
    except Exception as e:
        logger.error(f"Analyst agent failed: {e}")
        raise RuntimeError(f"Pipeline step 3 (Analyst) failed: {e}") from e
    
    result = {
        "fact": selection.selected_fact,
        "visual_concept": selection.visual_concept,
        "hook": selection.hook_phrase,
        "voiceover_script": "",
        "sources": [] # We need to aggregate sources from validated facts or selection
    }
    
    # Collect sources from the selected fact
    # Priority: Use sources from Analyst output (specific to selected fact)
    # Fallback: Aggregate from all validated facts
    final_sources = selection.sources
    
    if not final_sources:
        all_sources = set()
        for vf in validated_facts:
            for src in vf.sources:
                all_sources.add(src)
        final_sources = list(all_sources)
        
    result["sources"] = final_sources

    # Step 4: Write voiceover script
    logger.info("Agent 4 (Script Writer): Creating voiceover script...")
    try:
        script_result = await runner.run(
            script_writer,
            f"Write a voiceover script for this science video:\n\nFact: {result['fact']}\nVisual concept: {result['visual_concept']}\nHook phrase: {result['hook']}"
        )
        # Structured output: script_result.final_output is ScriptOutput
        script_data = script_result.final_output
        result["voiceover_script"] = script_data.voiceover_script
        
        logger.info(f"Script Writer created script ({len(result['voiceover_script'])} chars)")
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
    
    # Initialize sources list
    # (Will be populated from Analyst output or aggregation)
    sources = []
    
    runner = Runner()
    
    # Steps 1-3: Same as regular pipeline (research, evaluate, select)
    logger.info("Agent 1 (Researcher): Finding science facts...")
    try:
        research_result = await runner.run(
            researcher,
            "Find 5 mind-blowing science facts that would make great viral video content. Use web search to find real, verified facts."
        )
        # Structured output
        facts_list = research_result.final_output.facts
        if not facts_list:
            raise ValueError(f"Researcher returned empty list")
        
        # Serialize facts
        facts_text = "\n".join([f"{i+1}. [FACT]: {f.fact_text} [WHY INTERESTING]: {f.explanation}" for i, f in enumerate(facts_list)])
        logger.info(f"Researcher found {len(facts_list)} facts.")
    except Exception as e:
        raise RuntimeError(f"Pipeline step 1 (Researcher) failed: {e}") from e
    

    logger.info("Agent 2 (Evaluator): Validating facts...")
    try:
        eval_result = await runner.run(
            evaluator,
            f"Evaluate these science facts for accuracy and visual potential:\n\n{facts_text}"
        )
        # Structured output
        validated_facts = eval_result.final_output.validated_facts
        if not validated_facts:
             raise ValueError(f"Evaluator returned empty list")
             
        # Serialize for next agent
        validated_text = ""
        for vf in validated_facts:
            validated_text += f"- Fact: {vf.fact_text}\n  Scores: Acc={vf.accuracy_score}, Vis={vf.visualizability_score}, Wow={vf.wow_factor_score}\n  Notes: {vf.explanation}\n"
            # for src in vf.sources:
            #     sources.append(src) # Deferred: We'll get specific sources from Analyst
    except Exception as e:
        raise RuntimeError(f"Pipeline step 2 (Evaluator) failed: {e}") from e
    
    logger.info("Agent 3 (Analyst): Selecting best fact...")
    try:
        analyst_result = await runner.run(
            analyst,
            f"Select the single best science fact for a viral video:\n\n{validated_text}"
        )
        # Structured output
        selection = analyst_result.final_output
        logger.info(f"Analyst selected: {selection.selected_fact}")
    except Exception as e:
        raise RuntimeError(f"Pipeline step 3 (Analyst) failed: {e}") from e
    
    # Use selected fact
    fact = selection.selected_fact
    
    # Get sources from Analyst
    if selection.sources:
        sources = selection.sources
    else:
        # Fallback: recover sources by matching text or aggregating all
        # For extended pipeline, we really want specific sources, but aggregation is safe fallback
        all_s = set()
        for vf in validated_facts:
            for s in vf.sources:
                all_s.add(s)
        sources = list(all_s)
    
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
        # Structured output
        script_data = script_result.final_output
        voiceover_script = script_data.voiceover_script
        
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
        "sources": sources
    }
    
    logger.info(f"Extended pipeline complete. {len(scenes)} scenes, {total_duration}s total.")
    return result

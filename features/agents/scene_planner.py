from agents import Agent, function_tool, ModelSettings

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

def create_scene_planner_agent(num_scenes: int = 4) -> Agent:
    """Create the Scene Planner agent for multi-scene videos.
    
    Args:
        num_scenes: Number of scenes to generate (default 4 for ~32s video)
    """
    return Agent(
        name="ScenePlanner",
        model="o3-mini",
        model_settings=ModelSettings(
            reasoning={"effort": "medium"}
        ),
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

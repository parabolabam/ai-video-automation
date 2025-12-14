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
- ALL scenes must look like REAL raw footage (GoPro, IMAX, Documentary)
- Use REAL-WORLD references only (BBC Earth, NASA footage, National Geographic style)
- Describe REAL lighting imperfections (harsh sunlight, lens flares, chromatic aberration, sensor noise)
- Specify REAL camera equipment (ARRI Alexa 65, IMAX 70mm, RED V-Raptor, Macro Probe Lens)
- TEXTURE IS KEY: Mention pores, dust, scratches, organic irregularities. nothing smooth.

NEGATIVE CONSTRAINTS (Visuals to AVOID):
- NO "smooth", "perfect", "clean", or "glossy" AI looks
- NO "3d render", "octane render", "unreal engine", or "CGI"
- NO "cartoon", "illustration", "painting", or "abstract art"
- NO floating glowing objects unless chemically scientifically accurate

VISUAL CONSISTENCY across all scenes:
- Same color grading (Kodak 2383 Film Emulator style, high contrast, natural saturation)
- Same camera movement (handheld shake for intensity, slow drone for scale)
VISUAL FLOW & MATCHED CUTS (CRITICAL):
- Scene transitions must be SEAMLESS.
- The END frame of Scene N must logically connect to the START frame of Scene N+1.
- EXAMPLES:
  * Zoom into a cell -> Next scene starts inside the cell
  * Dolly past a planet -> Next scene continues movement in space
  * Focus on an eye -> Next scene is what the eye sees
- AVOID hard cuts between unrelated angles. Flow like a continuous single-take or matched cuts.

Scene structure:
- Scene 1: HOOK - Dramatic real-world opening shot (Macro or Wide)
- Scene 2-{num_scenes-1}: JOURNEY - Documentary-style exploration (Maintains motion/direction of previous scene)
- Scene {num_scenes}: PAYOFF - Stunning natural conclusion (Resolves the motion)

For EACH scene include:
1. Specific real-world location or setting (be tangible)
2. Exact lighting description (direction, quality, color)
3. Camera movement and lens type (focal length, depth of field)
4. Natural environmental details (dust, wind, texture)

Important: You MUST call the submit_scene_plan tool with your scenes to complete the task.
Pass the scenes as a LIST of strings, e.g. ["Scene 1 description...", "Scene 2 description..."].
Do not output text - call the tool with the structured arguments.""",
        tools=[submit_scene_plan],
    )

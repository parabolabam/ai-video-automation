from agents import Agent, ModelSettings
from features.agents.tools import fact_check, web_search
from features.agents.models import EvaluatorOutput

def create_evaluator_agent() -> Agent:
    """Create the Fact Evaluator agent."""
    return Agent(
        name="FactEvaluator",
        model="o3-mini",
        model_settings=ModelSettings(
            reasoning={"effort": "medium"}
        ),
        output_type=EvaluatorOutput,
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

Only include facts that score at least 7 on accuracy.
""",
        tools=[fact_check, web_search],
    )

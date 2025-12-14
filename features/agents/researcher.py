from agents import Agent, ModelSettings
from features.agents.tools import web_search, science_news_search
from features.agents.models import ResearcherOutput

def create_researcher_agent() -> Agent:
    """Create the Science Researcher agent."""
    return Agent(
        name="ScienceResearcher",
        model="o3-mini",
        model_settings=ModelSettings(
            reasoning={"effort": "medium"}
        ),
        output_type=ResearcherOutput,
        instructions="""You are a science researcher specializing in finding fascinating, mind-blowing science facts.

Your task is to find 5 interesting science facts that would make great short-form video content.

Guidelines:
- Look for facts that are visually representable
- Focus on topics like: space, physics, biology, chemistry, nature, technology
- Include both recent discoveries and timeless amazing facts
- Each fact should be simple enough to explain in 8 seconds
- Avoid controversial or unverified claims

Use the web_search and science_news_search tools to find facts.
""",
        tools=[web_search, science_news_search],
    )

from pydantic import BaseModel, Field
from typing import List

class ScienceFact(BaseModel):
    """A single science fact found by the researcher."""
    fact_text: str = Field(description="The scientific fact statement")
    explanation: str = Field(description="Brief explanation of why it is interesting")
    search_query_used: str = Field(description="The search query that found this fact")

class ResearcherOutput(BaseModel):
    """Output from the Researcher agent."""
    facts: List[ScienceFact] = Field(description="List of 5 interesting science facts")

class ValidatedFact(BaseModel):
    """A science fact validated by the evaluator."""
    fact_text: str = Field(description="The validated fact")
    accuracy_score: int = Field(description="Accuracy score (1-10)")
    visualizability_score: int = Field(description="Visualizability score (1-10)")
    wow_factor_score: int = Field(description="Wow factor score (1-10)")
    explanation: str = Field(description="Evaluator's notes on the fact")
    sources: List[str] = Field(description="List of source URLs used for verification")

class EvaluatorOutput(BaseModel):
    """Output from the Evaluator agent."""
    validated_facts: List[ValidatedFact] = Field(description="List of validated facts with scores")

class ViralContentSelection(BaseModel):
    """The single best fact selected by the Analyst."""
    selected_fact: str = Field(description="The winning science fact")
    visual_concept: str = Field(description="Brief description of how to visualize this")
    hook_phrase: str = Field(description="A compelling 5-word hook")
    reasoning: str = Field(description="Why this fact was selected")

class ScriptOutput(BaseModel):
    """Output from the Script Writer."""
    voiceover_script: str = Field(description="The complete spoken script text, without visual cues or labels")

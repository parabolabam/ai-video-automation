import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    print("Attempting to import pipeline from new location...")
    from features.agents.science_agents.pipeline import run_science_research_pipeline
    print("Successfully imported run_science_research_pipeline")
    
    from features.agents.science_agents import pipeline
    print("Successfully imported pipeline module")
    
    print("ALL CHECKS PASSED")
except Exception as e:
    print(f"IMPORT FAILED: {e}")
    sys.exit(1)


import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.getcwd())

from openai import AsyncOpenAI
from features.app.run_pipeline_v2 import run_pipeline_v2

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting local pipeline run...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment")
        return

    # Initialize OpenAI client
    client = AsyncOpenAI(api_key=api_key)
    
    # Run pipeline
    try:
        success = await run_pipeline_v2(client)
        if success:
            logger.info("Pipeline completed successfully!")
        else:
            logger.error("Pipeline finished with failure status.")
    except Exception as e:
        logger.error(f"Pipeline crashed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())

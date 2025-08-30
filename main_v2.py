#!/usr/bin/env python3
"""
AI Video Automation Orchestrator - v2 (Blotato-based posting)
"""

import asyncio
import sys
import logging
from features.core.load_env import load_env
from features.core.configure_logging import configure_logging
from features.core.setup_apis import setup_apis
from features.app.run_pipeline_v2 import run_pipeline_v2

logger = logging.getLogger(__name__)

load_env()
configure_logging()


clients = setup_apis()


async def main() -> None:
    try:
        ok = await run_pipeline_v2(clients["openai_client"])
        if not ok:
            logger.error("v2 pipeline failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Main v2 execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
CLI entrypoint for running platform workflows.

Usage:
  python3 -m features.platform.cli --workflow <UUID> --user <UUID> --input "Your input"
"""

import asyncio
import argparse
import logging
from dotenv import load_dotenv

from features.platform.runner import DynamicWorkflowRunner

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Run a dynamic platform workflow.")
    parser.add_argument("--workflow", required=True, help="Workflow UUID")
    parser.add_argument("--user", required=True, help="User UUID")
    parser.add_argument("--input", required=True, help="Initial input for the workflow")
    
    args = parser.parse_args()
    
    logger.info(f"Starting workflow {args.workflow} for user {args.user}")
    
    try:
        runner = DynamicWorkflowRunner(args.workflow, args.user)
        result = await runner.run(args.input)
        
        print("\n--- WORKFLOW COMPLETED ---")
        print(f"Status: {result.get('status')}")
        print(f"Final Output: {result.get('final_output')}")
        
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())

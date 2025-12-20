#!/usr/bin/env python3
"""
Dynamic Workflow Runner.

Executes a graph of agents defined in the database (Supabase).
"""

import logging
import json
import asyncio
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client
from agents import Agent, Runner

from features.openai.conversation_state import _get_supabase_client
from features.platform.tool_registry import get_tool_by_id

logger = logging.getLogger(__name__)

class DynamicWorkflowRunner:
    """Orchestrates the execution of a dynamic, database-driven workflow."""

    def __init__(self, workflow_id: str, user_id: str):
        self.workflow_id = workflow_id
        self.user_id = user_id
        self.supabase: Client = _get_supabase_client()
        self.agent_map: Dict[str, Agent] = {}
        self.connection_map: Dict[str, str] = {} # from_agent_id -> to_agent_id
        self.start_agent_id: Optional[str] = None

    async def build_graph(self):
        """Fetch configuration from DB and instantiate Agent objects."""
        logger.info(f"Building workflow graph for ID: {self.workflow_id}")

        # 1. Fetch Agents
        agents_resp = (
            self.supabase.table("agents")
            .select("*")
            .eq("workflow_id", self.workflow_id)
            .execute()
        )
        if not agents_resp.data:
            raise ValueError(f"No agents found for workflow {self.workflow_id}")

        for agent_data in agents_resp.data:
            self._instantiate_agent(agent_data)

        # 2. Fetch Connections
        conns_resp = (
            self.supabase.table("workflow_connections")
            .select("*")
            .eq("workflow_id", self.workflow_id)
            .execute()
        )
        
        for conn in conns_resp.data:
            from_id = conn.get("from_agent_id")
            to_id = conn.get("to_agent_id")
            
            if from_id is None:
                if self.start_agent_id is not None:
                     logger.warning(f"Multiple start points found. Overwriting {self.start_agent_id} with {to_id}")
                self.start_agent_id = to_id
            else:
                self.connection_map[from_id] = to_id

        if not self.start_agent_id:
            logger.warning("No start agent defined (connection with from_agent_id=NULL). Defaulting to first agent found.")
            if agents_resp.data:
                self.start_agent_id = agents_resp.data[0]["id"]


    def _instantiate_agent(self, data: Dict[str, Any]):
        """Create an Agent instance from DB row."""
        agent_id = data["id"]
        name = data["name"]
        model = data["model"]
        instructions = data["system_instructions"]
        tool_ids = data.get("tools") or []
        
        # Load tools from registry
        loaded_tools = []
        for tid in tool_ids:
            try:
                loaded_tools.append(get_tool_by_id(tid))
            except ValueError as e:
                logger.error(f"Skipping unknown tool '{tid}' for agent '{name}': {e}")

        # Instantiate
        # Note: We rely on string instructions. output_schema support can be added later if we dynamic loading of Pydantic models.
        agent = Agent(
            name=name,
            model=model,
            instructions=instructions,
            tools=loaded_tools,
        )
        
        self.agent_map[agent_id] = agent
        logger.debug(f"Instantiated Agent: {name} ({model})")


    async def run_stream(self, initial_input: str):
        """Execute the workflow yielding events."""
        if not self.agent_map:
            await self.build_graph()

        runner = Runner()
        
        # Determine start agent
        current_agent_id = self.start_agent_id
        if not current_agent_id or current_agent_id not in self.agent_map:
            yield {"type": "error", "content": "Could not determine valid start agent."}
            return
            
        current_input = initial_input
        history: List[Dict[str, Any]] = []

        # Execution Loop
        while current_agent_id:
            agent = self.agent_map[current_agent_id]
            logger.info(f"Running Agent: {agent.name}")
            
            # Emit Node Active Event
            yield {
                "type": "node_active", 
                "node_id": current_agent_id, 
                "agent_name": agent.name
            }
            
            try:
                # Run the agent
                # Note: If agent.run supported streaming, we would yield tokens here.
                # For now, we simulate thought streaming or just wait.
                result = await runner.run(agent, current_input)
                
                output_text = result.final_output
                if not isinstance(output_text, str):
                    output_text = str(output_text)

                history.append({
                    "agent": agent.name,
                    "output": output_text
                })
                
                # Emit Node Complete Event
                yield {
                    "type": "node_complete", 
                    "node_id": current_agent_id, 
                    "output": output_text
                }
                
                current_input = output_text
                current_agent_id = self.connection_map.get(current_agent_id)
                
            except Exception as e:
                logger.error(f"Execution failed at agent {agent.name}: {e}")
                yield {"type": "error", "content": str(e)}
                raise # Re-raise to stop connection

        yield {"type": "workflow_complete", "final_output": current_input}

    # Backward compatibility wrapper
    async def run(self, initial_input: str) -> Dict[str, Any]:
        """Execute (non-streaming legacy wrapper)."""
        final_output = None
        history = []
        async for event in self.run_stream(initial_input):
            if event["type"] == "node_complete":
                history.append({"output": event["output"]})
                final_output = event["output"]
        
        return {
            "status": "completed",
            "history": history, 
            "final_output": final_output
        }

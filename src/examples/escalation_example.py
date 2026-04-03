"""Escalation example.

Demonstrates routing to the EscalationNode by giving a prompt that
suggests the user wants human assistance.
"""

import asyncio
import uuid

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from travel_planner.main import get_compiled_travel_planner_graph, get_config
from travel_planner.models.state import TravelPlannerState


async def run() -> None:
    graph = get_compiled_travel_planner_graph()

    # Construct a strongly-typed state object instead of a loose dict
    state = TravelPlannerState(
        user_prompt="I need to speak with a human agent about a billing issue.",
        messages=[],
    )
    thread_id = f"escalation_example_{str(uuid.uuid4())[:12]}"
    config = get_config(thread_id=thread_id)

    # Pass the state as a dict (graph expects a mutable mapping matching the schema)
    result = await graph.ainvoke(input=state.model_dump(), config=config)
    print("Escalation response:", result.get("last_ai_message"))


if __name__ == "__main__":
    asyncio.run(run())

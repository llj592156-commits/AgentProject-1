"""Travel planner example demonstrating human-in-the-loop interruption.

Flow:
1. First prompt gives partial trip info -> graph extracts params, finds missing, routes through fix/human input.
2. Provide missing info (interruption) and resume to produce itinerary.

Note: The compiled graph was configured with an interrupt before the human input node.
We simulate this by calling the graph twice: first to reach interruption, second after supplying
additional user data.
"""

from __future__ import annotations
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import uuid

from travel_planner.main import get_compiled_travel_planner_graph, get_config
from travel_planner.models.state import TravelPlannerState

# NOTE: Depending on langgraph version, interrupt handling may raise a generic Exception
# when an interrupt_before node is hit. We catch broadly to simulate human input.


async def run() -> None:
    graph = get_compiled_travel_planner_graph()

    thread_id = f"travel_planner_human_loop_{str(uuid.uuid4())[:12]}"
    config = get_config(thread_id=thread_id)

    initial_state = TravelPlannerState(
        user_prompt="Plan a budget trip from Paris to Madrid next month from 10th to 20th.",  # Likely missing fields
        messages=[],
    )

    first_result = await graph.ainvoke(input=initial_state.model_dump(), config=config)

    if (
        first_result["missing_trip_params"] is not None
        and len(first_result["missing_trip_params"]) > 0
    ):
        print("Graph interrupted for human input as expected.")
        initial_state.user_prompt = "The budget is 1500 euros."
        first_result = await graph.ainvoke(input=initial_state.model_dump(), config=config)
    print("Final itinerary after human input:", first_result["last_ai_message"])


if __name__ == "__main__":
    asyncio.run(run())

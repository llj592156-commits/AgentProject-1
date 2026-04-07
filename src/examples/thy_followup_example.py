#ok
"""Turkish Airlines (THY) multi-step example.

Demonstrates routing to the TurkishAirlinesNode. Requires MCP credentials
and browser auth (Miles&Smiles) as described in README.
"""

from __future__ import annotations

import asyncio
import uuid

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from travel_planner.main import get_compiled_travel_planner_graph, get_config
from travel_planner.models.state import TravelPlannerState


async def run() -> None:
    graph = get_compiled_travel_planner_graph()

    thread_id = f"thy_example_{str(uuid.uuid4())[:12]}"
    config = get_config(thread_id=thread_id)

    # Initial airline-related query
    state = TravelPlannerState(
        user_prompt="Find me Turkish Airlines flights from IST to JFK next month.",
        messages=[],
    )
    result = await graph.ainvoke(input=state.model_dump(), config=config)
    print("THY first response:", result.get("last_ai_message"))

    state.user_prompt = "December 15th."
    result2 = await graph.ainvoke(input=state.model_dump(), config=config)
    print("THY follow-up response:", result2.get("last_ai_message"))

    # Follow-up (should remain in airline context, leveraging history)
    state.user_prompt = "Can you also check business class availability?"
    result3 = await graph.ainvoke(input=state.model_dump(), config=config)
    print("THY follow-up response:", result3.get("last_ai_message"))

    
if __name__ == "__main__":
    asyncio.run(run())

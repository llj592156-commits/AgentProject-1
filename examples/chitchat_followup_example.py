"""Chitchat example with a follow-up question.

This script demonstrates invoking the compiled travel planner graph
for a simple conversation that intentionally routes to the ChitchatNode.

Routing is handled implicitly by the RouterNode based on the user prompt.
"""

from __future__ import annotations

import asyncio
import uuid

from travel_planner.main import get_compiled_travel_planner_graph, get_config
from travel_planner.models.state import TravelPlannerState


async def run() -> None:
    graph = get_compiled_travel_planner_graph()

    thread_id = f"chitchat_example_{str(uuid.uuid4())[:12]}"
    config = get_config(thread_id=thread_id)

    # First user input (should route to chitchat)
    state = TravelPlannerState(
        user_prompt="Hey there! How's your day?",
        messages=[],
    )
    result = await graph.ainvoke(input=state.model_dump(), config=config)
    print("First response (chitchat):", result.get("last_ai_message"))

    # Follow-up user question - conversation persists via messages
    state.user_prompt = "Glad to hear! Can you tell me a random fun fact?"
    result2 = await graph.ainvoke(input=state.model_dump(), config=config)
    print("Follow-up response:", result2.get("last_ai_message"))


if __name__ == "__main__":
    asyncio.run(run())

"""Example: Using InfoSkill to gather travel information.

This example demonstrates how to use the InfoSkill to gather
travel-related information like weather forecasts.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path so we can import travel_planner modules
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from travel_planner.models.state import TravelPlannerState, TravelParams
from travel_planner.skills.base_skill import SkillContext
from travel_planner.skills.info_skill import InfoSkill


async def main():
    """Test InfoSkill execution."""
    print("=" * 50)
    print("InfoSkill Example - Gathering Travel Information")
    print("=" * 50)

    # Create mock state
    state = TravelPlannerState(
        user_prompt="我想去北京旅行，告诉我天气情况",
        travel_params=TravelParams(destination="江苏省苏州"),
        messages=[],
    )

    # Create skill context
    context = SkillContext(state=state)

    # Create and execute skill
    skill = InfoSkill()
    result = await skill.execute(context)

    # Print results
    print(f"\nSuccess: {result.success}")
    print(f"Message: {result.message}")
    print(f"\nData: {result.data}")
    print(f"\nState Updates: {result.state_updates}")
    print("=" * 50)


if __name__ == "__main__":         
    asyncio.run(main())

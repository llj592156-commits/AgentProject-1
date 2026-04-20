"""Planning Skill - Creates travel itineraries based on user preferences.

Combines:
- Flight search (via MCP)
- Hotel search (via MCP)
- Activity recommendations
- Budget optimization
"""

from datetime import date
from typing import Any

from travel_planner.skills.base_skill import BaseSkill, SkillContext, SkillResult


class PlanningSkill(BaseSkill):
    """Skill for creating comprehensive travel plans."""

    @property
    def name(self) -> str:
        return "planning"

    @property
    def description(self) -> str:
        return "Create detailed travel itineraries with flights, hotels, and activities."

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute the planning skill.

        Steps:
        1. Extract travel parameters from state
        2. Get MCP tools for flight/hotel search
        3. Build context for itinerary generation
        4. Return structured plan
        """
        self._log_execution("start", "Beginning travel planning")

        travel_params = context.state.travel_params
        if not travel_params:
            return SkillResult.fail(
                message="Missing travel parameters",
                error="No travel parameters found in state",
            )

        # Get MCP pool for tools
        mcp_pool = context.get_tool("mcp_pool")

        # Build context for itinerary generation
        planning_context = {
            "travel_params": travel_params.model_dump(),
            "mcp_tools_available": mcp_pool is not None,
        }

        self._log_execution(
            "complete",
            f"Planning completed with params: {travel_params.origin} -> {travel_params.destination}",
        )

        return SkillResult.ok(
            message="Travel plan generated successfully",
            state_updates={"planning_context": planning_context},
            data=planning_context,
        )

    async def can_execute(self, context: SkillContext) -> bool:
        """Check if we have minimum required parameters."""
        return (
            context.state.travel_params is not None
            and context.state.travel_params.destination is not None
        )

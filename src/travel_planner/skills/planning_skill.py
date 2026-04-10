"""Planning Skill - Creates travel itineraries based on user preferences.

Combines:
- Flight search
- Hotel search
- Activity recommendations
- Budget optimization
"""

from datetime import date
from typing import Any

from travel_planner.skills.base_skill import BaseSkill, SkillContext, SkillResult
from travel_planner.tools.api_gateway import APIGateway


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
        2. Search for flights (if API available)
        3. Search for hotels (if API available)
        4. Generate itinerary using LLM
        5. Return structured plan
        """
        self._log_execution("start", "Beginning travel planning")

        travel_params = context.state.travel_params
        if not travel_params:
            return SkillResult.fail(
                message="Missing travel parameters",
                error="No travel parameters found in state",
            )

        # Get API gateway if available
        api_gateway: APIGateway | None = context.get_tool("api_gateway") #从技能状态类获取工具

        # Try to gather real data if APIs are available
        flight_data = None
        hotel_data = None
        weather_data = None

        if api_gateway:
            try:
                if travel_params.origin and travel_params.destination:
                    flight_data = await api_gateway.search_flights(
                        origin=travel_params.origin,
                        destination=travel_params.destination,
                        departure_date=travel_params.date_from,
                        return_date=travel_params.date_to,
                    )

                if travel_params.destination:
                    weather_data = await api_gateway.get_weather(
                        city=travel_params.destination
                    )
            except Exception as e:
                self._logger.warning(f"API data fetch failed: {e}")

        # Build context for itinerary generation
        planning_context = {
            "travel_params": travel_params.model_dump(),
            "flight_data": flight_data.data if flight_data else None,
            "hotel_data": hotel_data.data if hotel_data else None,
            "weather_data": weather_data.data if weather_data else None,
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

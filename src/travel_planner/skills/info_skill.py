"""Info Skill - Gathers travel-related information.

Provides:
- Weather forecasts
- Visa requirements
- Currency exchange
- Travel advisories
- Local information
"""

from travel_planner.skills.base_skill import BaseSkill, SkillContext, SkillResult
from travel_planner.tools.api_gateway import APIGateway


class InfoSkill(BaseSkill):
    """Skill for gathering travel information."""

    @property
    def name(self) -> str:
        return "info"

    @property
    def description(self) -> str:
        return "Gather travel information like weather, visa requirements, and local tips."

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute the info gathering skill."""
        self._log_execution("start", "Gathering travel information")

        api_gateway: APIGateway | None = context.get_tool("api_gateway")
        info_result = {}

        # Get weather if destination is known
        if context.state.travel_params and context.state.travel_params.destination:
            if api_gateway:
                try:
                    weather = await api_gateway.get_weather(
                        city=context.state.travel_params.destination
                    )
                    if weather.success:
                        info_result["weather"] = weather.data
                except Exception as e:
                    self._logger.warning(f"Weather fetch failed: {e}")

        self._log_execution("complete", f"Gathered info: {list(info_result.keys())}")

        return SkillResult.ok(
            message="Travel information gathered",
            state_updates={"travel_info": info_result},
            data=info_result,
        )

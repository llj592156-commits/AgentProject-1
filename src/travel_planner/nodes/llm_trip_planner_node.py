#ok
from datetime import datetime

from travel_planner.helpers.llm_utils import invoke_llm
from travel_planner.models.available_llm_models import LLMs
from travel_planner.models.state import TravelPlannerState
from travel_planner.nodes.base_node import BaseNode
from travel_planner.prompts.prompt_handler import PromptTemplates
from travel_planner.orchestration.orchestrator import SkillOrchestrator


class LLMTripPlannerNode(BaseNode):
    """
    LLM Trip Planner Node - Uses Skill Orchestrator to plan trips.

    Instead of directly calling LLM, this node uses the SkillOrchestrator
    to execute the PlanningSkill which may use MCP tools.
    """

    def __init__(
        self,
        prompt_templates: PromptTemplates,
        llm_models: LLMs,
        skill_orchestrator: SkillOrchestrator | None = None,
    ):
        super().__init__()
        self.prompt_templates = prompt_templates
        self.llm_models = llm_models
        self._skill_orchestrator = skill_orchestrator

    async def async_run(self, state: TravelPlannerState) -> TravelPlannerState:
        tp = state.travel_params
        if (
            tp is None
            or tp.origin is None
            or tp.destination is None
            or tp.date_from is None
            or tp.date_to is None
            or tp.budget is None
        ):
            self.logger.warning("Missing travel parameters")
            raise ValueError("Missing travel parameters")

        # If skill orchestrator is available, use skills
        if self._skill_orchestrator:
            self.logger.info("Using SkillOrchestrator for trip planning")

            # Execute planning skill
            result = await self._skill_orchestrator.execute(
                state=state,
                skill_name="planning",
            )

            if result.success and result.data:
                # Use the skill result to generate final response
                planning_data = result.data

                # Format the planning data into a readable response
                response = self._format_planning_response(planning_data)
                state.last_ai_message = response
                state.messages.append(
                    HumanMessage(content=response)  # Or AIMessage if you prefer
                )
                return state

        # Fallback: Direct LLM call (backward compatible)
        self.logger.info("Using direct LLM call for trip planning")

        prompt_value = self.prompt_templates.trip_planner.format_prompt(
            today=datetime.today(),
            origin=tp.origin,
            destination=str(tp.destination),
            date_from=str(tp.date_from),
            date_to=str(tp.date_to),
            budget=str(tp.budget),
        )

        ai_message = await invoke_llm(
            prompt_value=prompt_value,
            response_model=None,
            llm=self.llm_models.large_model,
            messages_history=state.messages,
        )
        state.last_ai_message = str(ai_message.content)
        state.messages.append(ai_message)
        return state

    def _format_planning_response(self, data: dict) -> str:
        """Format planning data into a readable response."""
        lines = ["🗺️ Your Travel Plan\n"]

        if "summary" in data:
            summary = data["summary"]
            lines.append(f"From: {summary.get('origin', 'N/A')} → {summary.get('destination', 'N/A')}")
            lines.append(f"Duration: {summary.get('duration_days', 0)} days")
            lines.append(f"Budget: €{summary.get('total_budget', 0)} | Estimated: €{summary.get('estimated_total', 0)}\n")

        if "flight" in data and data["flight"]:
            flight = data["flight"]
            lines.append(f"✈️ Flight: {flight.get('flight_number', 'N/A')}")
            lines.append(f"   {flight.get('departure_time', '')} → {flight.get('arrival_time', '')}\n")

        if "hotel" in data and data["hotel"]:
            hotel = data["hotel"]
            lines.append(f"🏨 Hotel: {hotel.get('name', 'N/A')}")
            lines.append(f"   €{hotel.get('price_per_night', 0)}/night\n")

        if "daily_plan" in data:
            lines.append("📅 Daily Plan:")
            for day in data["daily_plan"]:
                lines.append(f"   Day {day['day']}: {day['activities'][0] if day['activities'] else 'Free time'}")

        return "\n".join(lines)

#ok
from langchain_core.messages import HumanMessage

from travel_planner.helpers.llm_utils import invoke_llm
from travel_planner.models.available_llm_models import LLMs
from travel_planner.models.router_models import Routes, RoutingDecision
from travel_planner.models.state import TravelPlannerState
from travel_planner.nodes.base_node import BaseNode
from travel_planner.prompts.prompt_handler import PromptTemplates


class RouterNode(BaseNode):
    """
    Router node that analyzes user input and decides whether the task is:
    - travel_planner: User wants to plan a trip
    - chitchat: General conversation/questions not related to travel planning
    - escalation: User wants to contact an agent or needs human assistance
    - turkish_airlines: User wants Turkish Airlines specific service
    """

    def __init__(
        self,
        prompt_templates: PromptTemplates,
        llm_models: LLMs,
    ):
        super().__init__()
        self.prompt_templates = prompt_templates
        self.llm_models = llm_models

    async def async_run(self, state: TravelPlannerState) -> TravelPlannerState:
        # Use LLM to determine the routing decision
        prompt_value = self.prompt_templates.routing_decision.format_prompt(
            user_message=state.user_prompt
        )

        # Get routing decision from LLM
        routing_decision = await invoke_llm(
            prompt_value=prompt_value,
            response_model=RoutingDecision,
            llm=self.llm_models.large_model,
            messages_history=state.messages,
        )

        if not isinstance(routing_decision, RoutingDecision):
            self.logger.error(
                f"LLM response could not be parsed into RoutingDecision: {routing_decision}"
            )
            # Default to chitchat if parsing fails
            routing_decision = RoutingDecision(
                predicted_route=Routes.CHITCHAT,
                reasoning="Failed to parse routing decision, defaulting to chitchat",
            )

        # Store the routing decision in state
        state.routing_decision = routing_decision

        self.logger.info(
            f"{self.node_id} | Routing decision: {routing_decision.predicted_route.value} "
            f"- {routing_decision.reasoning}"
        )
        user_message = HumanMessage(state.user_prompt)
        state.messages.append(user_message)
        return state

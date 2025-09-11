from travel_planner.models.available_llm_models import LLMs
from travel_planner.nodes.base_node import BaseNode
from travel_planner.models.state import TravelPlannerState
from travel_planner.models.router_models import RoutingDecision
from travel_planner.helpers.llm_utils import invoke_llm
from travel_planner.prompts.prompt_handler import PromptTemplates


class RouterNode(BaseNode):
    """
    Router node that analyzes user input and decides whether the task is:
    - travel_planner: User wants to plan a trip
    - chitchat: General conversation/questions not related to travel planning
    - escalation: User wants to contact an agent or needs human assistance
    """
    
    def __init__(self, prompt_templates: PromptTemplates, llm_models: LLMs):
        super().__init__()
        self.prompt_templates = prompt_templates
        self.llm_models = llm_models

    async def async_run(self, state: TravelPlannerState) -> TravelPlannerState:  # type: ignore[override]
        # Use LLM to determine the routing decision
        prompt_value = self.prompt_templates.routing_decision.format_prompt(
            user_message=state.user_prompt
        )
        
        # Get routing decision from LLM
        routing_decision = await invoke_llm(
            prompt_value=prompt_value,
            response_model=RoutingDecision,
            llm=self.llm_models.mini_model,
            messages_history=state.messages
        )
        
        if not isinstance(routing_decision, RoutingDecision):
            self.logger.error(f"LLM response could not be parsed into RoutingDecision: {routing_decision}")
            # Default to chitchat if parsing fails
            routing_decision = RoutingDecision(
                task_type="chitchat",
                confidence=0.5,
                reasoning="Failed to parse routing decision, defaulting to chitchat"
            )
        
        # Store the routing decision in state
        state.routing_decision = routing_decision
        
        self.logger.info(
            f"{self.node_id} | Routing decision: {routing_decision.task_type} "
            f"(confidence: {routing_decision.confidence:.2f}) - {routing_decision.reasoning}"
        )
        
        return state

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
        # Build conversation history for context-aware routing
        conversation_history = self._build_conversation_history(state.messages)

        # Build existing travel params summary if available
        existing_params = self._build_existing_params_summary(state.travel_params)

        # Use LLM to determine the routing decision with context
        prompt_value = self.prompt_templates.routing_decision.format_prompt(
            user_message=state.user_prompt,
            conversation_history=conversation_history,
            existing_travel_params=existing_params,
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

    def _build_conversation_history(self, messages: list) -> str:
        """
        Build a concise conversation history string from messages.
        Only includes the last few messages to avoid token bloat.
        """
        if not messages:
            return ""

        # Take last 6 messages (3 pairs of user/ai) for context
        recent_messages = messages[-6:]

        history_lines = []
        for msg in recent_messages:
            role = "用户" if hasattr(msg, 'type') and msg.type == "human" else "助手"
            if hasattr(msg, 'type') and msg.type == "ai":
                role = "助手"
            elif hasattr(msg, 'type') and msg.type == "human":
                role = "用户"
            else:
                # Fallback: check for role attribute
                role = "用户" if str(getattr(msg, 'type', 'human')) == 'human' else "助手"

            content = getattr(msg, 'content', str(msg))
            # Truncate long messages
            if len(content) > 100:
                content = content[:100] + "..."
            history_lines.append(f"{role}: {content}")

        return "\n".join(history_lines)

    def _build_existing_params_summary(self, travel_params) -> str:
        """
        Build a summary string of existing travel parameters.
        """
        if not travel_params:
            return ""

        params_dict = travel_params.model_dump() if hasattr(travel_params, 'model_dump') else {}
        if not params_dict:
            return ""

        # Filter out None values and format
        lines = []
        param_names = {
            "origin": "出发地",
            "destination": "目的地",
            "date_from": "出发日期",
            "date_to": "返回日期",
            "budget": "预算",
        }

        for key, value in params_dict.items():
            if value is not None:
                cn_name = param_names.get(key, key)
                lines.append(f"- {cn_name}: {value}")

        if not lines:
            return ""

        return "\n".join(lines)

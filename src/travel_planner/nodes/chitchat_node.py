from travel_planner.models.available_llm_models import LLMs
from travel_planner.nodes.base_node import BaseNode
from travel_planner.models.state import TravelPlannerState
from travel_planner.helpers.llm_utils import invoke_llm
from travel_planner.prompts.prompt_handler import PromptTemplates


class ChitchatNode(BaseNode):
    """
    Node that handles general conversation and non-travel related queries.
    Uses LLM to generate friendly responses to user messages.
    """
    
    def __init__(self, prompt_templates: PromptTemplates, llm_models: LLMs):
        super().__init__()
        self.prompt_templates = prompt_templates
        self.llm_models = llm_models

    async def async_run(self, state: TravelPlannerState) -> TravelPlannerState:  # type: ignore[override]
        # Generate chitchat response using LLM
        prompt_value = self.prompt_templates.chitchat_response.format_prompt(
            user_message=state.user_prompt
        )
        
        # Get response from LLM as BaseMessage (no structured output needed)
        response = await invoke_llm(
            prompt_value=prompt_value,
            response_model=None,
            llm=self.llm_models.mini_model,
            messages_history=state.messages
        )
        
        # Extract content from BaseMessage
        if hasattr(response, 'content'):
            content = response.content
            # Handle different content types
            if isinstance(content, str):
                response_text = content
            elif isinstance(content, list):
                # Join list elements if content is a list
                response_text = " ".join(str(item) for item in content)
            else:
                response_text = str(content)
        else:
            self.logger.error(f"LLM response does not have content attribute: {response}")
            response_text = "I'm here to help! Feel free to ask me anything or let me know if you'd like to plan a trip."
        
        # Store the chitchat response in state
        state.chitchat_response = response_text
        
        self.logger.info(f"{self.node_id} | Generated chitchat response")
        
        return state

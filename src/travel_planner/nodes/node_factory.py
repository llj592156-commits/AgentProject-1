
from travel_planner.models.available_openai_models import OpenAIModels
from travel_planner.nodes.collect_trip_params_node import CollectTripParamsNode
from travel_planner.nodes.hotel_params_llm_node import HotelParamsLLMNode
from travel_planner.nodes.hotel_search_node import HotelSearchNode
from travel_planner.prompts.prompt_handler import PromptTemplates


class NodeFactory:
    def __init__(self, prompt_templates: PromptTemplates, openai_models: OpenAIModels):
        # Common variables for some nodes
        self.prompt_templates = prompt_templates
        self.openai_models = openai_models
    
    @property
    def collect_trip_params_node(self):
        return CollectTripParamsNode()
    
    @property
    def hotel_params_llm_node(self) -> HotelParamsLLMNode:
        return HotelParamsLLMNode(
            prompt_templates=self.prompt_templates,
            openai_models=self.openai_models
        )
    
    @property
    def hotel_search_node(self) -> HotelSearchNode:
        return HotelSearchNode()
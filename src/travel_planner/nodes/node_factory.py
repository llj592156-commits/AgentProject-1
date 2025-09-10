
from functools import cached_property
from travel_planner.models.available_llm_models import LLMs
from travel_planner.nodes.extract_trip_params_node import ExtractTripParamsNode
from travel_planner.nodes.fix_trip_params_node import FixTripParamsNode
from travel_planner.nodes.trip_params_human_input_node import TripParamsHumanInputNode
from travel_planner.nodes.hotel_params_llm_node import HotelParamsLLMNode
from travel_planner.nodes.hotel_search_node import HotelSearchNode
from travel_planner.prompts.prompt_handler import PromptTemplates


class NodeFactory:
    def __init__(self, prompt_templates: PromptTemplates, llm_models: LLMs):
        # Common variables for some nodes
        self.prompt_templates = prompt_templates
        self.llm_models = llm_models
    
    @cached_property
    def extract_trip_params_node(self):
        return ExtractTripParamsNode(prompt_templates=self.prompt_templates, llm_models=self.llm_models)
    
    @cached_property
    def fix_trip_params_node(self):
        return FixTripParamsNode(prompt_templates=self.prompt_templates, llm_models=self.llm_models)

    @cached_property
    def trip_params_human_input_node(self):
        return TripParamsHumanInputNode()

    @cached_property
    def hotel_params_llm_node(self) -> HotelParamsLLMNode:
        return HotelParamsLLMNode(
            prompt_templates=self.prompt_templates,
            llm_models=self.llm_models
        )
    
    @cached_property
    def hotel_search_node(self) -> HotelSearchNode:
        return HotelSearchNode()
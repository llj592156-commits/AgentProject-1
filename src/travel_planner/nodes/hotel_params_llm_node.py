import math
from travel_planner.helpers.llm_utils import invoke_llm_with_structured_output
from travel_planner.models.available_openai_models import OpenAIModels
from travel_planner.nodes.base_node import BaseNode
from travel_planner.models.state import HotelAPIParams, TravelPlannerState
from travel_planner.prompts.prompt_handler import PromptTemplates
from dateutil import parser


class HotelParamsLLMNode(BaseNode):
    """
    Uses an LLM to fill Amadeus hotel-search parameters from the
    (validated) trip state.  Output is written into `state.api_params`.
    """
    def __init__(self, prompt_templates: PromptTemplates, openai_models: OpenAIModels):
        super().__init__()
        self.prompt_templates = prompt_templates
        self.openai_models = openai_models
    
    async def async_run(self, state: TravelPlannerState) -> TravelPlannerState:  # type: ignore[override]
        # Parse dates from string to datetime objects
        parsed_date_from = parser.parse(state.date_from).date()
        parsed_date_to = parser.parse(state.date_to).date()
        nights = max((parsed_date_to - parsed_date_from).days, 1)
        nightly_budget = state.budget / nights
        max_nightly = math.ceil(nightly_budget)

        prompt_value = self.prompt_templates.amadeus_hotel_search.invoke(
            {
                "destination": state.destination,
                "check_in_date": parsed_date_from.isoformat(),
                "check_out_date": parsed_date_to.isoformat(),
                "pax": state.pax,
                "max_nightly": max_nightly,
            }
        )
        
        # Call the helper that wraps your favourite LLM and validates against HotelAPIParams
        hotel_search_api_params: HotelAPIParams = await invoke_llm_with_structured_output(
            prompt_value=prompt_value,
            response_model=HotelAPIParams,
            llm=self.openai_models.gpt_4_1,
        )

        state.hotel_search_api_params = hotel_search_api_params
        self.logger.debug(f"LLM-generated hotel params: \n{state.hotel_search_api_params}")
        return state

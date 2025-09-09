
import uuid
from travel_planner.graphs.travel_planner_graph import TravelPlannerGraph
from travel_planner.helpers.llm_utils import get_available_llms
from travel_planner.models.state import TravelPlannerState
from travel_planner.nodes.node_factory import NodeFactory
from travel_planner.prompts.prompt_handler import PromptTemplates
from travel_planner.settings.settings_handler import AppSettings
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

def get_travel_planner_graph():
    prompt_templates = PromptTemplates.read_from_yaml()
    settings = AppSettings.read_from_yaml()
    llm_models = get_available_llms(settings=settings.openai)
    node_factory = NodeFactory(
        prompt_templates=prompt_templates,
        llm_models=llm_models
    )
    graph = TravelPlannerGraph(node_factory=node_factory)
    return graph.build_graph()

class TravelPlannerOrchestrator:
    def __init__(self, checkpointer: BaseCheckpointSaver):
        self.compiled_graph = get_travel_planner_graph().compile(checkpointer=checkpointer)
    
    async def ainvoke(self, config: RunnableConfig, first_state: TravelPlannerState) -> TravelPlannerState:
        response = await self.compiled_graph.ainvoke(
            config=config,
            input=first_state
        )
        return response

if __name__ == "__main__":
    # Example usage
    load_dotenv()
    checkpointer = MemorySaver()

    orchestrator = TravelPlannerOrchestrator(checkpointer=checkpointer)
    
    initial_state = TravelPlannerState(
        user_prompt="Plan a trip from Berlin to Paris"
    )
    
    import asyncio
    thread_id = str(uuid.uuid4())
    config = RunnableConfig({"configurable": {"thread_id": thread_id}})
    
    response = asyncio.run(orchestrator.ainvoke(config, initial_state))
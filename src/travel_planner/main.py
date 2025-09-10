import uuid
from travel_planner.graphs.travel_planner_graph import TravelPlannerGraph
from travel_planner.helpers.llm_utils import get_available_llms
from travel_planner.models.state import TravelPlannerState
from travel_planner.nodes.node_factory import NodeFactory
from travel_planner.prompts.prompt_handler import PromptTemplates
from travel_planner.settings.settings_handler import AppSettings
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv


def get_compiled_travel_planner_graph():
    prompt_templates = PromptTemplates.read_from_yaml()
    settings = AppSettings.read_from_yaml()
    llm_models = get_available_llms(settings=settings.openai)
    node_factory = NodeFactory(
        prompt_templates=prompt_templates,
        llm_models=llm_models
    )
    graph = TravelPlannerGraph(node_factory=node_factory)
    built_graph = graph.build_graph()
    compiled_graph = built_graph.compile(
        checkpointer=MemorySaver(),
        interrupt_before=[ 
            node_factory.trip_params_human_input_node.node_id # Human in the loop
        ]
    )
    return compiled_graph

class TravelPlannerOrchestrator:
    def __init__(self):
        self.compiled_graph = get_compiled_travel_planner_graph()
    
    async def ainvoke(self, config: RunnableConfig, state: TravelPlannerState) -> TravelPlannerState:
        response = await self.compiled_graph.ainvoke(
            config=config,
            input=state
        )
        response = TravelPlannerState(**response)
        return response
    
    async def continue_from_interrupt(self, config: RunnableConfig, updated_state: TravelPlannerState | None = None):
        """Continue execution after an interrupt, optionally updating the state first."""
        if updated_state:
            # Update the state at the interruption point
            await self.compiled_graph.aupdate_state(config, updated_state)
        
        # Continue execution from where it was interrupted
        final_events = []
        async for event in self.compiled_graph.astream(
            input=None,  # No new input needed
            config=config,
            stream_mode="values"
        ):
            final_events.append(event)
        
        return final_events[-1] if final_events else None

if __name__ == "__main__":
    """
    Human-in-the-Loop Travel Planner Example
    
    This example demonstrates how to handle interrupted execution in LangGraph:
    
    1. Start execution with incomplete information
    2. Get interrupted when human input is needed  
    3. Update the state with additional user information
    4. Continue execution from the interruption point
    
    Key methods for continuing interrupted flows:
    - aupdate_state(): Update state at interruption point
    - astream(): Continue execution from current state
    - continue_from_interrupt(): Helper method combining both
    """
    # Example usage with human-in-the-loop functionality
    load_dotenv()
    
    async def run_travel_planner_example():
        print("🌍 Travel Planner with Human-in-the-Loop Example")
        print("=" * 55)
        
        orchestrator = TravelPlannerOrchestrator()
        thread_id = str(uuid.uuid4())
        config = RunnableConfig({"configurable": {"thread_id": thread_id}})
        
        # Example 1: Incomplete request that needs human input
        print("\n📝 Example 1: Incomplete Request")
        print("-" * 30)
        user_prompt = "I want to plan a trip to Paris"
        print(f"   User: {user_prompt}")
        
        initial_state = TravelPlannerState(user_prompt=user_prompt)
        
        try:
            # First execution - should get interrupted
            print("\n⚡ Processing initial request...")
            result = await orchestrator.ainvoke(config, initial_state)
            
            # Check if we got interrupted (missing parameters)
            if result.missing_trip_params:
                print(f"\n⏸️  Execution interrupted - Missing parameters: {', '.join(result.missing_trip_params)}")

                # Simulate user providing additional information
                additional_info = "Origin: Berlin, dates: 2025-12-01 to 2025-12-05, budget: 800 EUR"
                print(f"\n   User provides: {additional_info}")
                
                # Update the state with new information
                result.user_prompt = additional_info
                
                # Continue execution from where it was interrupted
                print("\n⚡ Continuing with additional information...")
                
                # Method 1: Using the helper method
                final_result = await orchestrator.continue_from_interrupt(config, result)
                
                if final_result and final_result.travel_params:
                    print("\n✅ Travel planning completed!")
                    tp = final_result.travel_params
                    print(f"   📍 Origin: {tp.origin}")
                    print(f"   🎯 Destination: {tp.destination}")
                    print(f"   📅 From: {tp.date_from} to {tp.date_to}")
                    print(f"   💰 Budget: €{tp.budget}")
                else:
                    print(f"\n⚠️  Still having issues: {final_result.missing_trip_params if final_result else 'No result'}")
            else:
                print("\n✅ Travel planning completed in first attempt!")
                if result.travel_params:
                    tp = result.travel_params
                    print(f"   📍 Origin: {tp.origin}")
                    print(f"   🎯 Destination: {tp.destination}")
                    print(f"   📅 From: {tp.date_from} to {tp.date_to}")
                    print(f"   💰 Budget: €{tp.budget}")
        
        except Exception as e:
            print(f"\n❌ Error in Example: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 55)
        print("Example completed! 🎉")
    
    import asyncio
    asyncio.run(run_travel_planner_example())
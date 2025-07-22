# returns a Graph object
from pathlib import Path
from travel_planner.main import TravelPlannerOrchestrator
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
load_dotenv()

def draw_graph() -> None:
    # init orchestrator
    orchestrator = TravelPlannerOrchestrator(checkpointer=MemorySaver())

    # make sure docs/ exists
    docs_path = Path(__file__).parent.parent / "docs"
    docs_path.mkdir(exist_ok=True)

    # ⇩ note the extra `.get_graph()`
    orchestrator.compiled_graph.get_graph().draw_mermaid_png(
        output_file_path=docs_path / "langgraph.png"
    )

if __name__ == "__main__":
    draw_graph()
    print("Graph saved to docs/langgraph.png")
#ok
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

from contextlib import AsyncExitStack

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import CompiledStateGraph

from travel_planner.graphs.travel_planner_graph import TravelPlannerGraph
from travel_planner.helpers.llm_utils import get_available_llms
from travel_planner.nodes.node_factory import NodeFactory
from travel_planner.prompts.prompt_handler import PromptTemplates
from travel_planner.settings.settings_handler import AppSettings
from travel_planner.tools.mcp_client import MCPClientPool, TurkishAirlinesMCPConfig

# Global tool layer resources
_stack = AsyncExitStack()
_checkpointer = None
_mcp_pool: MCPClientPool | None = None


async def _get_or_create_mcp_pool() -> MCPClientPool:
    """Get or create the shared MCP connection pool."""
    global _mcp_pool
    if _mcp_pool is None:
        _mcp_pool = MCPClientPool()
        # Register Turkish Airlines connection from environment
        thy_config = TurkishAirlinesMCPConfig.from_env()
        _mcp_pool.register_connection(thy_config.to_mcp_connection())
    return _mcp_pool


async def get_compiled_travel_planner_graph() -> CompiledStateGraph:
    """Build and compile the travel planner graph with tool layer support."""
    global _checkpointer
    load_dotenv()

    # Load configurations
    prompt_templates = PromptTemplates.read_from_yaml()
    settings = AppSettings.read_from_yaml()
    llm_models = get_available_llms(settings=settings.openai)

    # Initialize tool layer
    mcp_pool = await _get_or_create_mcp_pool()

    # Create node factory with tool layer injection
    node_factory = NodeFactory(
        prompt_templates=prompt_templates,
        llm_models=llm_models,
        mcp_pool=mcp_pool,
    )

    # Build and compile graph
    graph = TravelPlannerGraph(node_factory=node_factory)
    built_graph = graph.build_graph()

    if _checkpointer is None:
        _checkpointer = await _stack.enter_async_context(
            AsyncSqliteSaver.from_conn_string("checkpoints202604071333.sqlite")
        )

    compiled_graph = built_graph.compile(
        checkpointer=_checkpointer,
        interrupt_before=[
            node_factory.trip_params_human_input_node.node_id  # Human in the loop
        ],
    )
    return compiled_graph


def get_config(thread_id: str) -> RunnableConfig:
    """Get runnable config for a given thread ID."""
    config = RunnableConfig(
        configurable={"thread_id": thread_id},
        metadata={"langfuse_session_id": thread_id},
    )
    return config

#ok
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import AsyncExitStack

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import CompiledStateGraph

from travel_planner.graphs.travel_planner_graph import TravelPlannerGraph
from travel_planner.helpers.llm_utils import get_available_llms
from travel_planner.nodes.node_factory import NodeFactory
from travel_planner.prompts.prompt_handler import PromptTemplates
from travel_planner.settings.settings_handler import AppSettings
from travel_planner.tools.mcp_client import MCPClientPool


# Global resources
_stack = AsyncExitStack()
_checkpointer = None
_mcp_pool: MCPClientPool | None = None


async def _get_or_create_mcp_pool() -> MCPClientPool:
    """Get or create the shared MCP connection pool."""
    global _mcp_pool
    if _mcp_pool is None:
        _mcp_pool = MCPClientPool()
        # Register all MCP servers
        from travel_planner.tools.mcp_client import MCPConnection

        # Flight MCP Server
        _mcp_pool.register_connection(MCPConnection(
            name="flights",
            transport="stdio",
            command=sys.executable,
            args=[r"D:\AgentProject\Project-1\langgraph-template-travel-planner\src\travel_planner\mcp_server\mock_thy_server.py"],
        ))

        # Hotel MCP Server
        _mcp_pool.register_connection(MCPConnection(
            name="hotels",
            transport="stdio",
            command=sys.executable,
            args=[r"D:\AgentProject\Project-1\langgraph-template-travel-planner\src\travel_planner\mcp_server\hotel_server.py"],
        ))

    return _mcp_pool


async def get_compiled_travel_planner_graph() -> CompiledStateGraph:
    """Build and compile the travel planner graph."""
    global _checkpointer
    load_dotenv()

    # Load configurations
    prompt_templates = PromptTemplates.read_from_yaml()
    settings = AppSettings.read_from_yaml()
    llm_models = get_available_llms(settings=settings.openai)

    # Initialize MCP connection pool (Tool layer)
    mcp_pool = await _get_or_create_mcp_pool()

    # Create node factory with MCP pool injected
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


async def main():
    """Main entry point for testing the travel planner.

    This function demonstrates how to use the travel planner graph
    with a sample user request.
    """
    import asyncio

    # Initialize the compiled graph
    print("Initializing travel planner graph...")
    compiled_graph = await get_compiled_travel_planner_graph()
    print("Graph initialized successfully!\n")

    # Test case 1: Travel planning request
    print("=" * 50)
    print("Test 1: Travel Planning Request")
    print("=" * 50)
    test_prompt = "帮我规划 6 月 1 日去四川省成都的旅行，预算 10000 元"

    config = get_config(thread_id="test-thread-001")

    try:
        result = await compiled_graph.ainvoke(
            input={"user_prompt": test_prompt, "messages": []},
            config=config,
        )
        print(f"AI: {result.get('last_ai_message', 'No response')}\n")
    except Exception as e:
        print(f"Error: {e}\n")

    # Test case 2: Chitchat request
    print("=" * 50)
    print("Test 2: Chitchat Request")
    print("=" * 50)
    test_prompt = "我将从上海出发，预计6月5日返回"

    # config = get_config(thread_id="test-thread-001")

    try:
        result = await compiled_graph.ainvoke(
            input={"user_prompt": test_prompt, "messages": []},
            config=config,
        )
        print(f"AI: {result.get('last_ai_message', 'No response')}\n")
    except Exception as e:
        print(f"Error: {e}\n")

    print("=" * 50)
    print("Tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

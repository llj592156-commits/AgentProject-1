#ok
from langchain_core.messages import AIMessage
from langchain.agents import create_agent

from travel_planner.models.available_llm_models import LLMs
from travel_planner.models.state import TravelPlannerState
from travel_planner.nodes.base_node import BaseNode
from travel_planner.prompts.prompt_handler import PromptTemplates
from travel_planner.tools.mcp_client import MCPClientPool, TurkishAirlinesMCPConfig


class TurkishAirlinesNode(BaseNode):
    """
    Node that handles Turkish Airlines specific queries and integrates with
    Turkish Airlines MCP server for flight information, bookings, and services.

    Uses the tool layer's MCPClientPool for connection management.
    """

    def __init__(
        self,
        prompt_templates: PromptTemplates,
        llm_models: LLMs,
        mcp_pool: MCPClientPool | None = None,
    ):
        super().__init__()
        self.prompt_templates = prompt_templates
        self.llm_models = llm_models

        # Use injected MCP pool or create one from environment
        self._mcp_pool = mcp_pool or MCPClientPool()
        self._mcp_config = TurkishAirlinesMCPConfig.from_env()
        self._turkish_airlines_agent = None

        # Register the Turkish Airlines connection
        self._mcp_pool.register_connection(self._mcp_config.to_mcp_connection())

        self.logger.info(
            f"TurkishAirlinesNode initialized - "
            f"Use Mock: {self._mcp_config.use_mock}"
        )

    async def _ensure_agent_initialized(self) -> None:
        """Initialize the Turkish Airlines agent if not already done."""
        if self._turkish_airlines_agent is None:
            try:
                tools = await self._mcp_pool.get_tools()
                self._turkish_airlines_agent = create_agent(
                    self.llm_models.large_model, tools
                )
                self.logger.info("Turkish Airlines MCP agent initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Turkish Airlines MCP agent: {e}")
                raise

    async def async_run(self, state: TravelPlannerState) -> TravelPlannerState:  # type: ignore[override]
        try:
            await self._ensure_agent_initialized()

            if self._turkish_airlines_agent is None:
                raise ValueError("Turkish Airlines MCP agent is not initialized")

            self.logger.info(
                f"{self.node_id} | Processing Turkish Airlines query: {state.user_prompt}"
            )

            agent_response = await self._turkish_airlines_agent.ainvoke(
                {"messages": state.messages}
            )

            if agent_response and "messages" in agent_response and len(agent_response["messages"]) > 0:
                ai_message = agent_response["messages"][-1]
                state.last_ai_message = str(ai_message.content)
                state.messages.append(ai_message)
                self.logger.info(f"{self.node_id} | Successfully processed Turkish Airlines query")
            else:
                self.logger.error("Empty or invalid response from Turkish Airlines agent")
                fallback_message = (
                    "I'm sorry, I couldn't process your Turkish Airlines request at the moment. "
                    "Please try again later."
                )
                ai_message = AIMessage(content=fallback_message)
                state.last_ai_message = fallback_message
                state.messages.append(ai_message)

        except Exception as e:
            self.logger.error(f"Error in TurkishAirlinesNode: {e}")
            error_message = (
                "I encountered an issue while processing your Turkish Airlines request. "
                "Please try again or contact support if the problem persists."
            )
            ai_message = AIMessage(content=error_message)
            state.last_ai_message = error_message
            state.messages.append(ai_message)

        return state

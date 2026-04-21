#ok
from datetime import datetime

from langchain_core.messages import AIMessage, SystemMessage

from travel_planner.models.available_llm_models import LLMs
from travel_planner.models.state import TravelPlannerState
from travel_planner.nodes.base_node import BaseNode
from travel_planner.prompts.prompt_handler import PromptTemplates
from travel_planner.tools.mcp_client import MCPClientPool


class LLMTripPlannerNode(BaseNode):
    """
    LLM Trip Planner Node - LLM with tool binding for trip planning.

    The LLM will:
    - Decide whether to call tools based on the request
    - Generate tool_calls for flight/hotel searches
    - Or generate final response if no tools needed

    Flow:
    - If LLM generates tool_calls -> ToolNode executes -> back to this node
    - If LLM generates final response -> finish
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
        self._mcp_pool = mcp_pool
        self._tools = None

    async def _ensure_tools_loaded(self) -> None:
        """Load MCP tools for binding."""
        if self._tools is None and self._mcp_pool:
            self._tools = await self._mcp_pool.get_tools()
            self.logger.info(f"LLMTripPlannerNode: Loaded {len(self._tools)} tools for binding")

    async def async_run(self, state: TravelPlannerState) -> TravelPlannerState:
        tp = state.travel_params
        if (
            tp is None
            or tp.origin is None
            or tp.destination is None
            or tp.date_from is None
            or tp.date_to is None
            or tp.budget is None
        ):
            self.logger.warning("Missing travel parameters")
            raise ValueError("Missing travel parameters")

        await self._ensure_tools_loaded()

        self.logger.info("Generating trip plan with LLM (with tool binding)")

        # Format prompt
        prompt_text = self.prompt_templates.trip_planner.format(
            today=datetime.today(),
            origin=tp.origin,
            destination=str(tp.destination),
            date_from=str(tp.date_from),
            date_to=str(tp.date_to),
            budget=str(tp.budget),
        )

        # Bind tools to LLM if available
        llm = self.llm_models.large_model
        if self._tools:
            llm_with_tools = llm.bind_tools(self._tools)
        else:
            llm_with_tools = llm

        # Build messages: system prompt as first message, then conversation history
        input_messages = [
            SystemMessage(content=prompt_text),
            *state.messages,
        ]

        # Invoke LLM with tools
        ai_message = await llm_with_tools.ainvoke(input_messages)
        # Store the message (may contain tool_calls or final response)
        state.messages.append(ai_message)
        has_tool_calls = getattr(ai_message, "tool_calls", None)
        state.last_ai_message = str(ai_message.content) if not has_tool_calls else "[工具调用中...]"

        return state

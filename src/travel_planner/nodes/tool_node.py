"""Tool Node - Pure tool execution node for LangGraph.

This node executes tools based on LLM-generated tool_calls.
It does NOT contain an LLM - it only executes tools and returns results.
"""

import json

from langchain_core.messages import ToolMessage

from travel_planner.models.state import TravelPlannerState
from travel_planner.nodes.base_node import BaseNode
from travel_planner.tools.mcp_client import MCPClientPool


class ToolNode(BaseNode):
    """
    Pure tool execution node.

    Usage:
    - Receives state with messages containing tool_calls from LLM
    - Executes each tool call
    - Returns ToolMessage results to be sent back to LLM

    This node should be used with tools_condition for routing:
    - LLM generates tool_calls -> ToolNode executes -> back to LLM
    - LLM generates final response -> finish
    """

    def __init__(
        self,
        mcp_pool: MCPClientPool | None = None,
        skill_tools: list | None = None,
    ):
        super().__init__()
        self._mcp_pool = mcp_pool
        self._skill_tools = skill_tools or []
        self._tools = None
        self._tools_by_name: dict = {}

        self.logger.info("ToolNode initialized (pure tool execution mode)")

    async def _ensure_tools_loaded(self) -> None:
        """Load MCP tools and Skill tools."""
        if self._tools is None:
            if self._mcp_pool is None:
                raise ValueError("MCP pool not configured")
            self._tools = await self._mcp_pool.get_tools()

        # Merge MCP tools with Skill tools
        all_tools = (self._tools or []) + self._skill_tools
        self._tools_by_name = {tool.name: tool for tool in all_tools}
        self.logger.info(f"ToolNode: Loaded {len(self._tools_by_name)} tools: {list(self._tools_by_name.keys())}")

    async def async_run(self, state: TravelPlannerState) -> TravelPlannerState:
        """Execute tools based on the last message's tool_calls.

        Args:
            state: Current state with messages

        Returns:
            State with added ToolMessage results
        """
        await self._ensure_tools_loaded()

        if not self._tools:
            raise ValueError("No MCP tools available")

        messages = state.messages
        if not messages:
            raise ValueError("No messages in state")

        # Get the last message (should be from LLM with tool_calls)
        last_message = messages[-1]
        self.logger.info(f"ToolNode: Last message content: {last_message.content}")
        # Extract tool_calls from the message
        tool_calls = getattr(last_message, "tool_calls", [])
        if not tool_calls:
            self.logger.warning("ToolNode: No tool_calls found in last message")
            return state

        self.logger.info(f"ToolNode: Executing {len(tool_calls)} tool call(s)")

        # Execute each tool call
        outputs = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            self.logger.info(f"ToolNode: Calling {tool_name} with {tool_args}")

            if tool_name not in self._tools_by_name:
                self.logger.error(f"ToolNode: Tool '{tool_name}' not found")
                result = f"Error: Tool '{tool_name}' not found"
            else:
                try:
                    # Execute the tool
                    tool_result = await self._tools_by_name[tool_name].ainvoke(tool_args)
                    # Extract content from result
                    if hasattr(tool_result, "content"):
                        result = str(tool_result.content)
                    else:
                        result = str(tool_result)

                    # # Log successful tool execution with result preview
                    # result_preview = result[:200] + "..." if len(result) > 200 else result
                    # self.logger.info(f"ToolNode: Tool '{tool_name}' executed successfully. Result: {result_preview}")
                except Exception as e:
                    self.logger.error(f"ToolNode: Tool '{tool_name}' execution failed: {e}")
                    result = f"Error: {str(e)}"

            # Create ToolMessage with result
            outputs.append(
                ToolMessage(
                    content=result,
                    name=tool_name,
                    tool_call_id=tool_call_id,
                )
            )

        # Add tool results to messages
        state.messages.extend(outputs)

        return state

    def get_tools(self):
        """Get loaded tools for use with LLM binding."""
        return self._tools or []

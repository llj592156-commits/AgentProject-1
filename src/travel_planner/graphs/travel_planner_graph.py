from __future__ import annotations  # 启用类型提示

from langgraph.graph import StateGraph

from travel_planner.helpers.logs import get_logger
from travel_planner.models.state import TravelPlannerState
from travel_planner.nodes.node_factory import NodeFactory


def check_for_tool_calls(state: TravelPlannerState) -> str:
    """Check if the last message has tool_calls.

    Returns:
        "continue" if tool_calls exist (need to execute tools)
        "finish" if no tool_calls (LLM generated final response)
    """
    if not state.messages:
        return "finish"

    last_message = state.messages[-1]
    tool_calls = getattr(last_message, "tool_calls", None)

    if tool_calls and len(tool_calls) > 0:
        return "continue"
    return "finish"


class TravelPlannerGraph:
    """
    Builds and compiles the LangGraph pipeline for the Gen-AI travel planner.
    """

    def __init__(self, node_factory: NodeFactory):
        self._nf = node_factory  # 节点工厂实例
        self.logger = get_logger()  # 日志记录器

    # --------------------------------------------------------------------- #
    # Public helpers
    # --------------------------------------------------------------------- #
    def build_graph(self) -> StateGraph:
        """Create, connect and compile the StateGraph with human-in-the-loop support."""
        graph = StateGraph(TravelPlannerState)
        graph = self._add_nodes(graph)
        graph = self._connect_edges(graph)
        return graph

    # --------------------------------------------------------------------- #
    # Internals
    # --------------------------------------------------------------------- #
    def _add_nodes(self, graph: StateGraph) -> StateGraph:
        """Register each node held by NodeFactory into the graph."""
        # Router Node - entry point
        graph.add_node(self._nf.router_node.node_id, self._nf.router_node.async_run)

        # Chitchat Node
        graph.add_node(self._nf.chitchat_node.node_id, self._nf.chitchat_node.async_run)

        # Escalation Node
        graph.add_node(self._nf.escalation_node.node_id, self._nf.escalation_node.async_run)

        # Tool Node - provides MCP tools for autonomous LLM tool calling
        graph.add_node(self._nf.tool_node.node_id, self._nf.tool_node.async_run)

        # Collect Trip Params Node
        graph.add_node(
            self._nf.extract_trip_params_node.node_id, self._nf.extract_trip_params_node.async_run
        )

        # Human Input Node for collecting missing information
        graph.add_node(
            self._nf.trip_params_human_input_node.node_id,
            self._nf.trip_params_human_input_node.async_run,
        )

        # LLM Trip Planner Node
        graph.add_node(
            self._nf.llm_trip_planner_node.node_id, self._nf.llm_trip_planner_node.async_run
        )

        return graph

    def _connect_edges(self, graph: StateGraph) -> StateGraph:
        """
        Wire the ordered execution flow with human-in-the-loop capability.

        Flow:
        Router -> [chitchat/escalation -> finish]
                -> [travel_planner -> ExtractTripParams -> LLMPlanner <-> ToolNode -> finish]

        ToolNode <-> LLMPlanner loop uses tools_condition for routing.
        """
        # Set router as entry point
        graph.set_entry_point(self._nf.router_node.node_id)

        # Router branches to chitchat, escalation, or extract_trip_params
        graph.add_conditional_edges(
            self._nf.router_node.node_id,
            self._decide_next_route,
            {
                self._nf.chitchat_node.node_id: self._nf.chitchat_node.node_id,
                self._nf.escalation_node.node_id: self._nf.escalation_node.node_id,
                self._nf.extract_trip_params_node.node_id: self._nf.extract_trip_params_node.node_id,
            },
        )

        # Chitchat and escalation nodes are end points
        graph.set_finish_point(self._nf.chitchat_node.node_id)
        graph.set_finish_point(self._nf.escalation_node.node_id)

        # After extraction, decide if we need human input or can proceed to planning
        graph.add_conditional_edges(
            self._nf.extract_trip_params_node.node_id,
            self._should_fix_trip_params,
            {
                self._nf.trip_params_human_input_node.node_id: self._nf.trip_params_human_input_node.node_id,
                self._nf.llm_trip_planner_node.node_id: self._nf.llm_trip_planner_node.node_id,
            },
        )

        # After human input, loop back to extract params to re-process with new info
        graph.add_edge(
            self._nf.trip_params_human_input_node.node_id, self._nf.extract_trip_params_node.node_id
        )

        # LLM Trip Planner Node -> check for tool_calls
        # If tool_calls exist -> ToolNode executes tools
        # If no tool_calls -> finish (LLM generated final response)
        graph.add_conditional_edges(
            self._nf.llm_trip_planner_node.node_id,
            check_for_tool_calls,
            {
                "continue": self._nf.tool_node.node_id,
                "finish": "__end__",
            },
        )

        # Tool Node -> back to LLM Trip Planner Node (for final response generation)
        graph.add_edge(
            self._nf.tool_node.node_id, self._nf.llm_trip_planner_node.node_id
        )

        return graph

    def _should_fix_trip_params(self, state: TravelPlannerState) -> str:
        """
        Decision function to determine if trip parameters need fixing.
        """
        if state.missing_trip_params and len(state.missing_trip_params) > 0:
            return self._nf.trip_params_human_input_node.node_id
        return self._nf.llm_trip_planner_node.node_id

    def _decide_next_route(self, state: TravelPlannerState) -> str:
        """
        Decide the next node using routing decision from RouterNode.
        """
        if state.routing_decision is None:
            return self._nf.chitchat_node.node_id

        route = state.routing_decision.predicted_route.value

        if route == "travel_planner":
            return self._nf.extract_trip_params_node.node_id
        elif route == "chitchat":
            return self._nf.chitchat_node.node_id
        elif route == "escalation":
            return self._nf.escalation_node.node_id
        else:
            return self._nf.escalation_node.node_id

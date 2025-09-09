from __future__ import annotations

from langgraph.graph import StateGraph
from travel_planner.models.state import TravelPlannerState
from travel_planner.nodes.node_factory import NodeFactory


class TravelPlannerGraph:
    """
    Builds and compiles the LangGraph pipeline for the Gen-AI travel planner.
    """

    def __init__(self, node_factory: NodeFactory):
        # Create a shortcut, normally it's not a good practice but it will be used 
        # frequently in this class.
        self._nf = node_factory
    
    # --------------------------------------------------------------------- #
    # Public helpers
    # --------------------------------------------------------------------- #
    def build_graph(self) -> StateGraph:
        """Create, connect and compile the StateGraph."""
        graph = StateGraph(TravelPlannerState)
        graph = self._add_nodes(graph)
        graph = self._connect_edges(graph)
        return graph

    # --------------------------------------------------------------------- #
    # Internals
    # --------------------------------------------------------------------- #
    def _add_nodes(self, graph: StateGraph) -> StateGraph:
        """Register each node held by NodeFactory into the graph."""
        # Collect Trip Params Node
        graph.add_node(self._nf.collect_trip_params_node.node_id, self._nf.collect_trip_params_node.async_run)
        
        # Fix Trip Params Node if necessary
        graph.add_node(self._nf.fix_trip_params_node.node_id, self._nf.fix_trip_params_node.async_run)
        
        # Register Hotel Params LLM Node
        graph.add_node(self._nf.hotel_params_llm_node.node_id, self._nf.hotel_params_llm_node.async_run)
        
        # Register Hotel Search Node
        graph.add_node(self._nf.hotel_search_node.node_id, self._nf.hotel_search_node.async_run)
        return graph

    def _connect_edges(self, graph: StateGraph) -> StateGraph:
        """
        Wire the ordered execution flow.
        For now we keep it linear:
            hotel_params  ─►  hotel_search
        Extend this method as you add more nodes & branches.
        """
        graph.set_entry_point(self._nf.collect_trip_params_node.node_id)
        
        graph.add_edge(self._nf.collect_trip_params_node.node_id,
                       self._nf.fix_trip_params_node.node_id)
        
        graph.add_edge(self._nf.hotel_params_llm_node.node_id,
                          self._nf.hotel_search_node.node_id)
        
        graph.set_finish_point(self._nf.hotel_search_node.node_id)
        return graph
    
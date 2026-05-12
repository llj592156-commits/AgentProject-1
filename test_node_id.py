"""
检查节点 ID 的实际值
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from travel_planner.nodes.node_factory import NodeFactory
from travel_planner.prompts.prompt_handler import PromptTemplates
from travel_planner.helpers.llm_utils import get_available_llms
from travel_planner.settings.settings_handler import AppSettings

settings = AppSettings.read_from_yaml()
llm_models = get_available_llms(settings=settings.openai)
prompt_templates = PromptTemplates.read_from_yaml()

nf = NodeFactory(prompt_templates=prompt_templates, llm_models=llm_models)

print("=== 节点 ID 检查 ===")
print(f"router_node.node_id: {nf.router_node.node_id}")
print(f"chitchat_node.node_id: {nf.chitchat_node.node_id}")
print(f"escalation_node.node_id: {nf.escalation_node.node_id}")
print(f"extract_trip_params_node.node_id: {nf.extract_trip_params_node.node_id}")
print(f"trip_params_human_input_node.node_id: {nf.trip_params_human_input_node.node_id}")
print(f"llm_trip_planner_node.node_id: {nf.llm_trip_planner_node.node_id}")
print(f"tool_node.node_id: {nf.tool_node.node_id}")

# 检查 _decide_next_route 返回的值
from travel_planner.models.router_models import Routes, RoutingDecision
from travel_planner.models.state import TravelParams, TravelPlannerState
from datetime import date

state = TravelPlannerState(
    user_prompt="如果我想去都江堰呢",
    messages=[],
    travel_params=TravelParams(
        origin="苏州",
        destination="成都",
        date_from=date(2026, 6, 1),
        date_to=date(2026, 6, 3),
        budget=3000.0
    ),
    routing_decision=RoutingDecision(
        predicted_route=Routes.TRAVEL_PLANNER,
        reasoning="测试"
    )
)

print("\n=== _decide_next_route 返回值 ===")
from travel_planner.graphs.travel_planner_graph import TravelPlannerGraph
graph_builder = TravelPlannerGraph(node_factory=nf)
result = graph_builder._decide_next_route(state)
print(f"_decide_next_route 返回：{result}")
print(f"期望的节点 ID: {nf.llm_trip_planner_node.node_id}")
print(f"是否匹配：{result == nf.llm_trip_planner_node.node_id}")

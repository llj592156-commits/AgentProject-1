from functools import cached_property

from travel_planner.models.available_llm_models import LLMs
from travel_planner.nodes.chitchat_node import ChitchatNode
from travel_planner.nodes.escalation_node import EscalationNode
from travel_planner.nodes.extract_trip_params_node import ExtractTripParamsNode
from travel_planner.nodes.fix_trip_params_node import FixTripParamsNode
from travel_planner.nodes.llm_trip_planner_node import LLMTripPlannerNode
from travel_planner.nodes.router_node import RouterNode
from travel_planner.nodes.trip_params_human_input_node import TripParamsHumanInputNode
from travel_planner.nodes.turkish_airlines_node import TurkishAirlinesNode
from travel_planner.prompts.prompt_handler import PromptTemplates
from travel_planner.tools.mcp_client import MCPClientPool


class NodeFactory:
    """Factory for creating all node instances with shared dependencies.

    Tool Layer Integration:
    - Manages shared MCPClientPool across nodes
    - Supports dependency injection for testability
    """

    def __init__(
        self,
        prompt_templates: PromptTemplates,
        llm_models: LLMs,
        mcp_pool: MCPClientPool | None = None,
    ):
        # Common variables for some nodes
        self.prompt_templates = prompt_templates  # 提示模板实例
        self.llm_models = llm_models     # LLM 模型实例
        self._mcp_pool = mcp_pool  # Shared MCP connection pool

    @cached_property
    def extract_trip_params_node(self) -> ExtractTripParamsNode:
        """旅行参数提取节点，以及缺失参数处理"""
        return ExtractTripParamsNode(
            prompt_templates=self.prompt_templates, llm_models=self.llm_models
        )

    @cached_property
    def fix_trip_params_node(self) -> FixTripParamsNode:
        """修复旅行参数提取节点"""
        return FixTripParamsNode(
            prompt_templates=self.prompt_templates, llm_models=self.llm_models
        )

    @cached_property
    def trip_params_human_input_node(self) -> TripParamsHumanInputNode:
        """旅行参数人类输入节点"""
        return TripParamsHumanInputNode()

    @cached_property
    def router_node(self) -> RouterNode:
        """路由节点"""
        return RouterNode(
            prompt_templates=self.prompt_templates, llm_models=self.llm_models
        )

    @cached_property
    def chitchat_node(self) -> ChitchatNode:
        """聊天节点"""
        return ChitchatNode(
            prompt_templates=self.prompt_templates, llm_models=self.llm_models
        )

    @cached_property
    def escalation_node(self) -> EscalationNode:
        """升级节点"""
        return EscalationNode()

    @cached_property
    def turkish_airlines_node(self) -> TurkishAirlinesNode:
        """土耳其航空公司节点"""
        return TurkishAirlinesNode(
            prompt_templates=self.prompt_templates,
            llm_models=self.llm_models,
            mcp_pool=self._mcp_pool,
        )

    @cached_property
    def llm_trip_planner_node(self) -> LLMTripPlannerNode:
        """LLM 旅行计划节点"""
        return LLMTripPlannerNode(
            prompt_templates=self.prompt_templates, llm_models=self.llm_models
        )

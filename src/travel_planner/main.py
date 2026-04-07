#ok
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
# from langfuse.langchain import CallbackHandler

from contextlib import AsyncExitStack

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import CompiledStateGraph

from travel_planner.graphs.travel_planner_graph import TravelPlannerGraph
from travel_planner.helpers.llm_utils import get_available_llms
from travel_planner.nodes.node_factory import NodeFactory
from travel_planner.prompts.prompt_handler import PromptTemplates
from travel_planner.settings.settings_handler import AppSettings

_stack = AsyncExitStack()
_checkpointer = None

async def get_compiled_travel_planner_graph() -> CompiledStateGraph:
    global _checkpointer
    load_dotenv()
    prompt_templates = PromptTemplates.read_from_yaml() #读取全部提示词
    settings = AppSettings.read_from_yaml() #读取大模型全部设置
    llm_models = get_available_llms(settings=settings.openai) #获取可用的LLM模型
    node_factory = NodeFactory(prompt_templates=prompt_templates, llm_models=llm_models) #创建节点工厂
    graph = TravelPlannerGraph(node_factory=node_factory) #创建结点流程图类
    built_graph = graph.build_graph() #构建图
    
    if _checkpointer is None:
        # 使用持久化的 SQLite 存储，并通过全局栈保持连接开启
        _checkpointer = await _stack.enter_async_context(
            AsyncSqliteSaver.from_conn_string("checkpoints202604071333.sqlite")
        )
    
    compiled_graph = built_graph.compile(
        checkpointer=_checkpointer,
        interrupt_before=[
            node_factory.trip_params_human_input_node.node_id  # Human in the loop
        ],
    ) #编译图
    return compiled_graph

#获取可运行配置
def get_config(thread_id: str) -> RunnableConfig:
    # langfuse_handler = CallbackHandler()
    config = RunnableConfig(
        configurable={"thread_id": thread_id},
        # callbacks=[langfuse_handler],
        metadata={"langfuse_session_id": thread_id},
    )
    return config

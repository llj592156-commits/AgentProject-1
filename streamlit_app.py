"""
Streamlit UI for Travel Planner with multi-turn conversation history support.
参考 main.py 的实现方式，直接调用 LangGraph
"""
import asyncio
import os
import sys
from datetime import datetime

import streamlit as st

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from dotenv import load_dotenv

load_dotenv()

from travel_planner.graphs.travel_planner_graph import TravelPlannerGraph
from travel_planner.helpers.llm_utils import get_available_llms
from travel_planner.nodes.node_factory import NodeFactory
from travel_planner.prompts.prompt_handler import PromptTemplates
from travel_planner.settings.settings_handler import AppSettings
from travel_planner.tools.mcp_client import MCPClientPool, MCPConnection


def init_session_state():
    """初始化 session state"""
    if "threads" not in st.session_state:
        st.session_state.threads = []
    if "current_thread_id" not in st.session_state:
        st.session_state.current_thread_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "initialized" not in st.session_state:
        st.session_state.initialized = False


def format_time(dt: datetime) -> str:
    """格式化时间显示"""
    now = datetime.now()
    diff = (now - dt).total_seconds()

    if diff < 60:
        return "刚刚"
    elif diff < 3600:
        return f"{int(diff // 60)} 分钟前"
    elif diff < 86400:
        return f"{int(diff // 3600)} 小时前"
    else:
        return dt.strftime("%m-%d %H:%M")


async def run_graph(thread_id: str, user_prompt: str, message_history: list) -> str:
    """
    运行 LangGraph 并返回 AI 响应。
    每次调用都创建新的资源实例，避免 Streamlit 重新运行问题。
    """
    # Load configurations
    prompt_templates = PromptTemplates.read_from_yaml()
    settings = AppSettings.read_from_yaml()
    llm_models = get_available_llms(settings=settings.openai)

    # Initialize MCP connection pool (每次创建新的)
    mcp_pool = MCPClientPool()

    # Flight MCP Server
    mcp_pool.register_connection(MCPConnection(
        name="flights",
        transport="stdio",
        command=sys.executable,
        args=[os.path.join(os.path.dirname(__file__), 'src', 'travel_planner', 'mcp_server', 'mock_thy_server.py')],
    ))

    # Hotel MCP Server
    mcp_pool.register_connection(MCPConnection(
        name="hotels",
        transport="stdio",
        command=sys.executable,
        args=[os.path.join(os.path.dirname(__file__), 'src', 'travel_planner', 'mcp_server', 'hotel_server.py')],
    ))

    # Create node factory with MCP pool injected
    node_factory = NodeFactory(
        prompt_templates=prompt_templates,
        llm_models=llm_models,
        mcp_pool=mcp_pool,
    )

    # Build and compile graph
    graph = TravelPlannerGraph(node_factory=node_factory)
    built_graph = graph.build_graph()

    # Create new checkpointer for each invocation
    async with AsyncSqliteSaver.from_conn_string("checkpoints202604071333.sqlite") as checkpointer:
        compiled_graph = built_graph.compile(
            checkpointer=checkpointer,
            interrupt_before=[
                node_factory.trip_params_human_input_node.node_id  # Human in the loop
            ],
        )

        config = {
            "configurable": {"thread_id": thread_id},
            "metadata": {"langfuse_session_id": thread_id},
        }

        # 调用图，传入消息历史
        result = await compiled_graph.ainvoke(
            input={"user_prompt": user_prompt, "messages": message_history},
            config=config,
        )

        return result.get("last_ai_message", "抱歉，我没有理解您的问题。")


# 初始化
init_session_state()

# 侧边栏
with st.sidebar:
    st.title("💬 历史会话")

    # 新建会话按钮
    if st.button("➕ 新建会话", use_container_width=True, key="new_thread"):
        new_id = f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.current_thread_id = new_id
        st.session_state.messages = []
        st.session_state.threads.insert(0, {
            "id": new_id,
            "title": "新会话",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        st.rerun()

    st.divider()

    # 会话列表
    for thread in st.session_state.threads:
        thread_id = thread["id"]
        title = thread.get("title", "新会话") or "新会话"

        is_selected = thread_id == st.session_state.current_thread_id

        if st.button(
            f"📄 {title[:18]}{'...' if len(title) > 18 else ''}",
            key=f"thread_{thread_id}",
            use_container_width=True,
            type="primary" if is_selected else "secondary"
        ):
            st.session_state.current_thread_id = thread_id
            st.session_state.messages = []  # 清空当前显示的消息
            st.rerun()

# 主界面
st.title("✈️ 旅行规划助手")
st.caption("帮您规划行程、查询航班和酒店信息")

# 确保有当前会话 ID
if not st.session_state.current_thread_id:
    new_id = f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.current_thread_id = new_id
    st.session_state.threads.insert(0, {
        "id": new_id,
        "title": "新会话",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    })

# 显示消息历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 聊天输入
if prompt := st.chat_input("输入您的问题，例如：我想去巴黎旅游..."):
    thread_id = st.session_state.current_thread_id

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)

    # 添加到消息历史
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 更新会话标题（如果是第一条消息）
    if len(st.session_state.messages) == 1:
        for thread in st.session_state.threads:
            if thread["id"] == thread_id:
                thread["title"] = prompt[:30]
                break

    # 获取 AI 响应
    with st.chat_message("assistant"):
        with st.spinner("正在思考..."):
            try:
                # 转换消息历史为 LangChain 格式
                langchain_messages = []
                for msg in st.session_state.messages[:-1]:  # 不包括当前用户消息
                    if msg["role"] == "user":
                        langchain_messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        langchain_messages.append(AIMessage(content=msg["content"]))

                response = asyncio.run(run_graph(thread_id, prompt, langchain_messages))
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.markdown(f"抱歉，发生错误：{str(e)}")

# 快捷查询
st.divider()
st.subheader("💡 快捷查询")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🇯🇵 日本旅游", use_container_width=True, key="jp_travel"):
        prompt = "我想去日本旅游，预算 20000 元"
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner("正在思考..."):
                try:
                    langchain_messages = []
                    for msg in st.session_state.messages[:-1]:
                        if msg["role"] == "user":
                            langchain_messages.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant":
                            langchain_messages.append(AIMessage(content=msg["content"]))
                    response = asyncio.run(run_graph(st.session_state.current_thread_id, prompt, langchain_messages))
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.markdown(f"抱歉，发生错误：{str(e)}")
        st.rerun()

with col2:
    if st.button("✈️ 查询航班", use_container_width=True, key="flight_query"):
        prompt = "帮我查一下上海到北京的航班"
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner("正在思考..."):
                try:
                    langchain_messages = []
                    for msg in st.session_state.messages[:-1]:
                        if msg["role"] == "user":
                            langchain_messages.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant":
                            langchain_messages.append(AIMessage(content=msg["content"]))
                    response = asyncio.run(run_graph(st.session_state.current_thread_id, prompt, langchain_messages))
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.markdown(f"抱歉，发生错误：{str(e)}")
        st.rerun()

with col3:
    if st.button("🗼 景点推荐", use_container_width=True, key="attraction_query"):
        prompt = "推荐一些巴黎的景点"
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner("正在思考..."):
                try:
                    langchain_messages = []
                    for msg in st.session_state.messages[:-1]:
                        if msg["role"] == "user":
                            langchain_messages.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant":
                            langchain_messages.append(AIMessage(content=msg["content"]))
                    response = asyncio.run(run_graph(st.session_state.current_thread_id, prompt, langchain_messages))
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.markdown(f"抱歉，发生错误：{str(e)}")
        st.rerun()

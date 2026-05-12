"""
Streamlit UI for Travel Planner with multi-turn conversation history support.
"""
import asyncio
import os
import sys
from datetime import datetime
from typing import Optional

import streamlit as st
import httpx

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 页面配置
st.set_page_config(
    page_title="旅行规划助手",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 样式
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .sidebar-content {
        background-color: #f8f9fa;
    }
    .new-thread-btn {
        width: 100%;
        margin-bottom: 10px;
    }
    .thread-item {
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 5px;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .thread-item:hover {
        background-color: #e9ecef;
    }
    .thread-item.selected {
        background-color: #0066cc;
        color: white;
    }
    .thread-title {
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .thread-time {
        font-size: 0.75em;
        color: #6c757d;
    }
    .quick-query-btn {
        border: 1px solid #dee2e6;
        background-color: white;
        border-radius: 20px;
        padding: 8px 16px;
        font-size: 0.9em;
    }
    .quick-query-btn:hover {
        background-color: #f1f3f5;
    }
</style>
""", unsafe_allow_html=True)

# 后端 API 地址
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# 初始化 session state
if "threads" not in st.session_state:
    st.session_state.threads = []
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False


def get_available_thread_id() -> str:
    """生成或获取可用的 thread_id"""
    if st.session_state.current_thread_id:
        return st.session_state.current_thread_id
    return f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def load_threads() -> list:
    """从后端加载会话列表"""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE}/api/threads")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        st.error(f"加载会话列表失败：{e}")
    return []


def load_messages(thread_id: str) -> list:
    """加载指定会话的消息历史"""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE}/api/threads/{thread_id}/messages")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        st.error(f"加载消息历史失败：{e}")
    return []


def send_message(thread_id: str, message: str) -> Optional[str]:
    """发送消息并获取回复"""
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{API_BASE}/api/chat",
                json={"thread_id": thread_id, "message": message}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response") or data.get("last_ai_message")
    except Exception as e:
        st.error(f"发送消息失败：{e}")
    return None


def create_new_thread() -> str:
    """创建新会话"""
    thread_id = f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{API_BASE}/api/threads",
                json={"thread_id": thread_id, "title": "新会话"}
            )
            if response.status_code == 200:
                return thread_id
    except Exception as e:
        st.error(f"创建会话失败：{e}")
    return thread_id


def update_thread_title(thread_id: str, title: str):
    """更新会话标题"""
    try:
        with httpx.Client(timeout=10.0) as client:
            client.put(
                f"{API_BASE}/api/threads/{thread_id}/title",
                json={"title": title}
            )
    except Exception as e:
        pass  # 静默失败，不影响用户体验


def format_time(dt_str: str) -> str:
    """格式化时间显示"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = (now - dt).total_seconds()

        if diff < 60:
            return "刚刚"
        elif diff < 3600:
            return f"{int(diff // 60)} 分钟前"
        elif diff < 86400:
            return f"{int(diff // 3600)} 小时前"
        else:
            return dt.strftime("%m-%d %H:%M")
    except:
        return dt_str


def init_app():
    """初始化应用"""
    if st.session_state.initialized:
        return

    st.session_state.initialized = True
    st.session_state.threads = load_threads()

    if not st.session_state.threads:
        # 创建默认会话
        thread_id = create_new_thread()
        st.session_state.threads = [{
            "id": thread_id,
            "title": "新会话",
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }]
        st.session_state.current_thread_id = thread_id
    else:
        # 加载最近的会话
        st.session_state.current_thread_id = st.session_state.threads[0]["id"]


# 侧边栏 - 会话列表
with st.sidebar:
    st.title("💬 历史会话")

    # 新建会话按钮
    if st.button("➕ 新建会话", use_container_width=True, key="new_thread"):
        thread_id = create_new_thread()
        new_thread = {
            "id": thread_id,
            "title": "新会话",
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        st.session_state.threads.insert(0, new_thread)
        st.session_state.current_thread_id = thread_id
        st.rerun()

    st.divider()

    # 会话列表
    if st.session_state.threads:
        for thread in st.session_state.threads:
            thread_id = thread["id"]
            title = thread.get("title", "新会话") or "新会话"
            updated_at = thread.get("updatedAt", "")

            # 选中状态样式
            is_selected = thread_id == st.session_state.current_thread_id

            # 使用列来创建可点击区域
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(
                    f"📄 {title[:20]}{'...' if len(title) > 20 else ''}",
                    key=f"thread_{thread_id}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.current_thread_id = thread_id
                    st.rerun()

            # 时间显示
            if updated_at:
                with col2:
                    st.caption(format_time(updated_at)[:6])

            st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
    else:
        st.info("暂无历史会话")

# 主界面
init_app()

# 标题
st.title("✈️ 旅行规划助手")
st.caption("帮您规划行程、查询航班和酒店信息")

# 获取当前会话的消息历史
current_messages = []
if st.session_state.current_thread_id:
    current_messages = load_messages(st.session_state.current_thread_id)

# 显示消息历史
# 过滤掉 system 消息，只显示 user 和 assistant 消息
display_messages = [
    msg for msg in current_messages
    if msg.get("role") in ["user", "assistant"]
]

for msg in display_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 聊天输入
if prompt := st.chat_input("输入您的问题，例如：我想去巴黎旅游..."):
    if not st.session_state.current_thread_id:
        st.error("请先创建或选择一个会话")
        st.stop()

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)

    # 发送消息到后端
    with st.chat_message("assistant"):
        with st.spinner("正在思考..."):
            # 调用后端 API
            response = asyncio.run(
                send_message_async(st.session_state.current_thread_id, prompt)
            ) if False else send_message(st.session_state.current_thread_id, prompt)

            if response:
                st.markdown(response)
                # 更新会话标题（如果是第一条消息）
                if len(display_messages) == 0:
                    update_thread_title(
                        st.session_state.current_thread_id,
                        prompt[:30]
                    )
                    # 更新本地线程列表
                    for thread in st.session_state.threads:
                        if thread["id"] == st.session_state.current_thread_id:
                            thread["title"] = prompt[:30]
                            break
            else:
                st.markdown("抱歉，发生错误，请稍后重试。")

# 快捷查询按钮
st.divider()
st.subheader("💡 快捷查询")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🇯🇵 日本旅游", use_container_width=True):
        st.session_state.quick_query = "我想去日本旅游，预算 20000 元"
        st.rerun()
with col2:
    if st.button("✈️ 查询航班", use_container_width=True):
        st.session_state.quick_query = "帮我查一下上海到北京的航班"
        st.rerun()
with col3:
    if st.button("🗼 景点推荐", use_container_width=True):
        st.session_state.quick_query = "推荐一些巴黎的景点"
        st.rerun()

# 处理快捷查询
if hasattr(st.session_state, 'quick_query') and st.session_state.quick_query:
    query = st.session_state.quick_query
    st.session_state.quick_query = None  # 清除标记

    if not st.session_state.current_thread_id:
        st.error("请先创建或选择一个会话")
        st.stop()

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(query)

    # 发送消息到后端
    with st.chat_message("assistant"):
        with st.spinner("正在思考..."):
            response = send_message(st.session_state.current_thread_id, query)

            if response:
                st.markdown(response)
                # 更新会话标题（如果是第一条消息）
                if len(display_messages) == 0:
                    update_thread_title(
                        st.session_state.current_thread_id,
                        query[:30]
                    )
            else:
                st.markdown("抱歉，发生错误，请稍后重试。")

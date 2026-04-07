#ok
#这是一个注释
"""Chitchat example with a follow-up question.

This script demonstrates invoking the compiled travel planner graph
for a simple conversation that intentionally routes to the ChitchatNode.

Routing is handled implicitly by the RouterNode based on the user prompt.
"""

from __future__ import annotations

import asyncio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, AIMessage
from travel_planner.main import get_compiled_travel_planner_graph, get_config
from travel_planner.models.state import TravelPlannerState


async def run() -> None:
    graph = await get_compiled_travel_planner_graph()

    # 使用固定的 thread_id，这样每次运行都会读取同一个“存档”
    thread_id = "persistent_chat_user_001"
    config = get_config(thread_id=thread_id)

    # --- 数据库持久化展示逻辑 ---
    # 检查数据库中是否已经存在该用户的历史状态
    current_state = await graph.aget_state(config)
    
    if current_state.values:
        print(f"--- 发现历史记忆 (Thread ID: {thread_id}) ---")
        last_msg = current_state.values.get("last_ai_message")
        print(f"上一轮 AI 最后说的是: {last_msg}")
        print("-------------------------------------------\n")
    else:
        print(f"--- 新会话开始 (Thread ID: {thread_id}) ---\n")

    # 第一轮对话
    state = TravelPlannerState(
        user_prompt="上一次我的提问是什么？",
        messages=[HumanMessage(content="你好，你能做什么"),
        AIMessage(content="你好")]
    )
    # ainvoke 会自动将结果存入 checkpoints.sqlite
    result = await graph.ainvoke(input=state.model_dump(), config=config)
    # print(result)
    print("First response (chitchat):", result.get("last_ai_message"))

    # # 第二轮对话
    # state.user_prompt = "Glad to hear! Can you tell me a random fun fact?"
    # result2 = await graph.ainvoke(input=state.model_dump(), config=config)
    # print("Follow-up response:", result2.get("last_ai_message"))


if __name__ == "__main__":
    asyncio.run(run())

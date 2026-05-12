"""
测试都江堰 bug 复现脚本
"""
import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from dotenv import load_dotenv
load_dotenv()

from travel_planner.main import get_compiled_travel_planner_graph, get_config


async def main():
    """测试多轮对话中的都江堰问题"""
    print("初始化旅行规划图...")
    compiled_graph = await get_compiled_travel_planner_graph()
    print("图初始化成功!\n")

    thread_id = "test-dujiangyan-bug"
    config = get_config(thread_id=thread_id)

    # 第一次请求 - 成都 3 日游
    print("=" * 60)
    print("测试 1: 成都 3 日游规划")
    print("=" * 60)
    test_prompt_1 = "我 6 月 1 日到 6 月 3 日想从苏州出发去成都旅游，预算 3000 元"

    try:
        result1 = await compiled_graph.ainvoke(
            input={"user_prompt": test_prompt_1, "messages": []},
            config=config,
        )
        print(f"AI 响应：{result1.get('last_ai_message', 'No response')}\n")
        messages_after_1 = result1.get('messages', [])
        print(f"消息数量：{len(messages_after_1)}\n")
    except Exception as e:
        print(f"测试 1 错误：{e}\n")
        import traceback
        traceback.print_exc()
        return

    # 第二次请求 - 想去都江堰
    print("=" * 60)
    print("测试 2: 用户追问'如果我想去都江堰呢'")
    print("=" * 60)
    test_prompt_2 = "如果我想去都江堰呢"

    try:
        result2 = await compiled_graph.ainvoke(
            input={"user_prompt": test_prompt_2, "messages": messages_after_1},
            config=config,
        )
        print(f"AI 响应：{result2.get('last_ai_message', 'No response')}\n")
    except Exception as e:
        print(f"测试 2 错误：{e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

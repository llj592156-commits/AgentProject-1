import asyncio
import os

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

load_dotenv()
NODE22_BIN = os.getenv("NODE_BIN_PATH")
MCP_REMOTE = os.getenv("MCP_REMOTE_COMMAND")


async def main() -> None:
    env = os.environ.copy()
    # Ensure /usr/bin/env node resolves to Node 22
    env["PATH"] = f"{NODE22_BIN}:{env.get('PATH', '')}"

    client = MultiServerMCPClient(
        {
            "turkish_airlines": {
                "transport": "stdio",
                "command": MCP_REMOTE,
                "args": ["https://mcp.turkishtechlab.com/sse", "--auth-timeout", "120", "--debug"],
                "env": env,
            }
        }
    )

    tools = await client.get_tools()
    print("Loaded tools:", [t.name for t in tools])

    llm = ChatOpenAI(model="gpt-4o-mini")
    agent = create_react_agent(llm, tools)
    out = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "show me the flights for brussels to istanbul"}]}
    )
    print(out["messages"][-1].content)


asyncio.run(main())

import asyncio, os
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
NODE22_BIN = "/Users/baturayofluoglu/.nvm/versions/node/v22.19.0/bin"
MCP_REMOTE = "/Users/baturayofluoglu/.nvm/versions/node/v22.19.0/bin/mcp-remote"

async def main():
    env = os.environ.copy()
    # Ensure /usr/bin/env node resolves to Node 22
    env["PATH"] = f"{NODE22_BIN}:{env.get('PATH','')}"

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
    out = await agent.ainvoke({"messages": [{"role":"user","content":"show me the flights for brussels to istanbul"}]})
    print(out["messages"][-1].content)

asyncio.run(main())
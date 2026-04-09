"""MCP Client Pool - Manages connections to multiple MCP servers."""
#ok
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Optional
from contextlib import asynccontextmanager

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool

from travel_planner.tools.base_tool import ToolResult, ToolConfig
from travel_planner.helpers.logs import get_logger


@dataclass
class MCPConnection:
    """Configuration for a single MCP connection."""

    name: str
    transport: str = "stdio"
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] | None = None
    url: str | None = None  # For SSE transport

    def to_dict(self) -> dict[str, Any]:
        """Convert to MCP client configuration dict."""
        config: dict[str, Any] = {"transport": self.transport}

        if self.transport == "stdio":
            if self.command:
                config["command"] = self.command
            if self.args:
                config["args"] = self.args
        elif self.transport == "sse":
            if self.url:
                config["url"] = self.url

        if self.env:
            config["env"] = self.env

        return config

#管理多个MCP服务器连接  
class MCPClientPool:
    """Pool of MCP connections with lazy initialization.

    Usage:
        pool = MCPClientPool()
        pool.register_connection(MCPConnection(...))
        tools = await pool.get_tools()
    """

    def __init__(self, config: ToolConfig | None = None):
        self._connections: dict[str, MCPConnection] = {} #连接的mcp服务器
        self._client: MultiServerMCPClient | None = None
        self._logger = get_logger()
        self._tools: list[BaseTool] | None = None

    def register_connection(self, connection: MCPConnection) -> None:
        """Register a new MCP connection configuration."""
        self._connections[connection.name] = connection
        self._client = None  # Invalidate cached client
        self._tools = None

    def unregister_connection(self, name: str) -> None:
        """Remove a connection by name."""
        if name in self._connections:
            del self._connections[name]
            self._client = None
            self._tools = None

    #获取工具
    async def get_tools(self) -> list[BaseTool]:
        """Get all tools from registered MCP servers.

        Lazily initializes the MCP client on first call.
        """
        if self._tools is not None:
            return self._tools

        if not self._connections:
            self._logger.warning("MCPClientPool: No connections registered")
            return []

        try:
            self._client = await self._create_client()
            self._tools = await self._client.get_tools()
            tool_names = [t.name for t in self._tools]
            self._logger.info(f"MCPClientPool: Loaded {len(self._tools)} tools: {tool_names}")
            return self._tools
        except Exception as e:
            self._logger.error(f"MCPClientPool: Failed to load tools: {e}")
            raise

    async def _create_client(self) -> MultiServerMCPClient:
        """Create and configure the MCP client."""
        """"
        生成的配置示例：
        {
            "turkish_airlines": {
                "transport": "sse",
                "url": "https://mcp.turkishtechlab.com/sse"
            },
            "hotel_booking": {
                "transport": "stdio",
                "command": "python",
                "args": ["hotel_server.py"]
            }
        }
        """
        client_config = {
            name: conn.to_dict() for name, conn in self._connections.items()
        }
        return MultiServerMCPClient(client_config)

    # 作用：从环境变量自动创建连接池
    @classmethod
    def from_env(cls, prefix: str = "") -> "MCPClientPool":
        """Create pool from environment variables.

        Environment variables:
        - {prefix}MCP_SERVERS: Comma-separated list of server names
        - {prefix}MCP_{NAME}_TRANSPORT: Transport type (stdio/sse)
        - {prefix}MCP_{NAME}_COMMAND: Command for stdio transport
        - {prefix}MCP_{NAME}_ARGS: Space-separated arguments
        - {prefix}MCP_{NAME}_URL: URL for SSE transport
        """
        pool = cls()
        servers = os.getenv(f"{prefix}MCP_SERVERS", "")

        if servers:
            for name in servers.split(","):
                name = name.strip()
                transport = os.getenv(f"{prefix}MCP_{name.upper()}_TRANSPORT", "stdio")
                command = os.getenv(f"{prefix}MCP_{name.upper()}_COMMAND")
                args_str = os.getenv(f"{prefix}MCP_{name.upper()}_ARGS", "")
                url = os.getenv(f"{prefix}MCP_{name.upper()}_URL")

                connection = MCPConnection(
                    name=name,
                    transport=transport,
                    command=command,
                    args=args_str.split() if args_str else [],
                    url=url,
                )
                pool.register_connection(connection)

        return pool


@dataclass
class TurkishAirlinesMCPConfig:
    """Configuration for Turkish Airlines MCP."""

    node_bin_path: str = ""
    mcp_remote_command: str = "mcp-remote"
    use_mock: bool = False
    mock_script_path: str = ""
    sse_url: str = "https://mcp.turkishtechlab.com/sse"
    auth_timeout: int = 120

    @classmethod
    def from_env(cls) -> "TurkishAirlinesMCPConfig":
        """Load configuration from environment."""
        return cls(
            node_bin_path=os.getenv("NODE_BIN_PATH", ""),
            mcp_remote_command=os.getenv("MCP_REMOTE_COMMAND", "mcp-remote"),
            use_mock=os.getenv("USE_MOCK_THY", "false").lower() == "true",
            mock_script_path=os.getenv(
                "MOCK_THY_PATH",
                "d:/AgentProject/Project-1/langgraph-template-travel-planner/mock_thy_server.py",
            ),
        )

    def to_mcp_connection(self) -> MCPConnection:
        """Convert to MCPConnection."""
        env = os.environ.copy()
        if self.node_bin_path:
            env["PATH"] = f"{self.node_bin_path}{os.pathsep}{env.get('PATH', '')}"

        if self.use_mock:
            return MCPConnection(
                name="turkish_airlines",
                transport="stdio",
                command=sys.executable,
                args=[self.mock_script_path],
                env=env,
            )
        else:
            return MCPConnection(
                name="turkish_airlines",
                transport="sse",
                url=self.sse_url,
                args=["--auth-timeout", str(self.auth_timeout)],
                env=env,
            )

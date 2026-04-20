"""Tool Layer - Unified interfaces for external services and tools.

This module provides:
- MCP client management (MultiServerMCPClient wrapper)
- Caching and rate limiting
"""

from travel_planner.tools.mcp_client import MCPClientPool, MCPConnection
from travel_planner.tools.base_tool import BaseTool, ToolResult, ToolConfig

__all__ = [
    "MCPClientPool",
    "MCPConnection",
    "BaseTool",
    "ToolResult",
    "ToolConfig",
]

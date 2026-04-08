"""Tool Layer - Unified interfaces for external services and tools.

This module provides:
- MCP client management (MultiServerMCPClient wrapper)
- Third-party API gateway (flights, hotels, weather, etc.)
- Caching and rate limiting
"""

from travel_planner.tools.mcp_client import MCPClientPool, MCPConnection
from travel_planner.tools.api_gateway import APIGateway, APIClient
from travel_planner.tools.base_tool import BaseTool, ToolResult, ToolConfig

__all__ = [
    "MCPClientPool",
    "MCPConnection",
    "APIGateway",
    "APIClient",
    "BaseTool",
    "ToolResult",
    "ToolConfig",
]

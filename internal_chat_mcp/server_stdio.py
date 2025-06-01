"""internal_chat_mcp MCP Server implementation."""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more verbosity
    format="[%(levelname)s] %(message)s",
    stream=sys.stderr,
)

from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any

from internal_chat_mcp.services.tool_service import ToolService
from internal_chat_mcp.services.resource_service import ResourceService
from internal_chat_mcp.interfaces.tool import Tool

# from internal_chat_mcp.interfaces.resource import Resource
from internal_chat_mcp.tools import (
    SendMessageTool,
    GetUnreadMessagesTool,
    WaitForMessageTool,
    GetRecentMessagesTool,
    GetVersionTool,
)

# from internal_chat_mcp.resources import HelloWorldResource, UserProfileResource
from internal_chat_mcp import __version__


def get_available_tools() -> List[Tool]:
    """Get list of all available tools."""
    return [
        SendMessageTool(),
        GetUnreadMessagesTool(),
        WaitForMessageTool(),
        GetRecentMessagesTool(),
        GetVersionTool(),
    ]


# def get_available_resources() -> List[Resource]:
#     """Get list of all available resources."""
#     return [
#         HelloWorldResource(),
#         UserProfileResource(),
#     ]


def main():
    """Entry point for the server."""
    logging.info(f"[internal_chat_mcp] MCP Server starting, version {__version__}")
    mcp = FastMCP("internal_chat_mcp")
    tool_service = ToolService()
    resource_service = ResourceService()

    # Register all tools and their MCP handlers
    tool_service.register_tools(get_available_tools())
    tool_service.register_mcp_handlers(mcp)

    # Register all resources and their MCP handlers
    # resource_service.register_resources(get_available_resources())
    # resource_service.register_mcp_handlers(mcp)

    mcp.run()


if __name__ == "__main__":
    main()

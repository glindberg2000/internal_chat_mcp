"""internal_chat_mcp MCP Server implementation."""

__version__ = "0.2.8"

print("=== DEBUG: server_stdio.py loaded ===")

import logging
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Set up logging to include version in every log line
logging.basicConfig(
    format=f"%(asctime)s [%(levelname)s] [v{__version__}] %(message)s",
    level=logging.INFO,
)

logging.info(f"[internal_chat_mcp] MCP STDIO Server starting, version {__version__}")

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


def get_manifest():
    tools = get_available_tools()
    return {
        "version": "1.0",
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_model.model_json_schema(),
                "output_schema": (
                    tool.output_model.model_json_schema()
                    if hasattr(tool, "output_model") and tool.output_model
                    else None
                ),
            }
            for tool in tools
        ],
    }


app = FastAPI()


@app.get("/mcp/manifest")
async def manifest():
    return JSONResponse(get_manifest())


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

    # Start FastAPI server for manifest endpoint
    uvicorn.run(app, host="0.0.0.0", port=6969, log_level="info", reload=False)

    # mcp.run()  # Optionally keep this if you want to run the original MCP server logic


if __name__ == "__main__":
    main()

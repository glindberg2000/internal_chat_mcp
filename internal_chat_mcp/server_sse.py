"""internal_chat_mcp MCP Server implementation with SSE transport."""

print("=== DEBUG: server_sse.py loaded ===")

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
from typing import List, Dict, Any
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from internal_chat_mcp.services.tool_service import ToolService
from internal_chat_mcp.services.resource_service import ResourceService
from internal_chat_mcp.interfaces.tool import Tool

# from internal_chat_mcp.interfaces.resource import Resource
from internal_chat_mcp.tools import (
    SendMessageTool,
    GetUnreadMessagesTool,
    WaitForMessageTool,
)

# from internal_chat_mcp.resources import HelloWorldResource, UserProfileResource

import internal_chat_mcp
import logging

# Set up logging to include version in every log line
logging.basicConfig(
    format=f"%(asctime)s [%(levelname)s] [v0.2.7] %(message)s",
    level=logging.INFO,
)

logging.info(f"[internal_chat_mcp] MCP SSE Server starting, version 0.2.7")


def get_available_tools() -> List[Tool]:
    """Get list of all available tools."""
    return [
        SendMessageTool(),
        GetUnreadMessagesTool(),
        WaitForMessageTool(),
    ]


# def get_available_resources() -> List[Resource]:
#     """Get list of all available resources."""
#     return [
#         HelloWorldResource(),
#         UserProfileResource(),
#     ]


def create_starlette_app(mcp_server: Server) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )
    ]

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        middleware=middleware,
    )


# Initialize FastMCP server with SSE
mcp = FastMCP("internal_chat_mcp")
tool_service = ToolService()
resource_service = ResourceService()

# Register all tools and their MCP handlers
tool_service.register_tools(get_available_tools())
tool_service.register_mcp_handlers(mcp)

# Register all resources and their MCP handlers
# resource_service.register_resources(get_available_resources())
# resource_service.register_mcp_handlers(mcp)

# Get the MCP server
mcp_server = mcp._mcp_server  # noqa: WPS437

# Create the Starlette app
app = create_starlette_app(mcp_server)

# Export the app
__all__ = ["app"]


def main():
    """Entry point for the server."""
    import argparse

    parser = argparse.ArgumentParser(description="Run MCP SSE-based server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=6969, help="Port to listen on")
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    args = parser.parse_args()

    # Run the server with auto-reload if enabled
    uvicorn.run(
        "internal_chat_mcp.server_sse:app",  # Use the app from server_sse.py directly
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=["internal_chat_mcp"],  # Watch this directory for changes
        timeout_graceful_shutdown=5,  # Add timeout
    )


if __name__ == "__main__":
    main()

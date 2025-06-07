"""
test_get_unread_messages.py

Test script for verifying MCP tool and backend chat server connectivity.

USAGE:
    python test_get_unread_messages.py [backend_host] [team_id] [user]

    # All defaults (localhost:8000, t24, Cline)
    python test_get_unread_messages.py

    # Set backend host only
    python test_get_unread_messages.py host.docker.internal:8000

    # Set backend host, team, and user via args
    python test_get_unread_messages.py host.docker.internal:8000 myteam myuser

    # Or use environment variables
    export BACKEND_HOST=host.docker.internal:8000
    export TEAM_ID=myteam
    export USER=myuser
    python test_get_unread_messages.py

This script is the recommended way to verify that your MCP tool and backend are communicating correctly in any environment.
"""

import asyncio
import os
import sys
from internal_chat_mcp.tools.send_message import SendMessageTool, SendMessageInput
from internal_chat_mcp.tools.get_unread_messages import (
    GetUnreadMessagesTool,
    GetUnreadMessagesInput,
    MessageFilter,
)


def get_arg_or_env(idx, env_var, default):
    # idx: 1-based index in sys.argv (after script name)
    if len(sys.argv) > idx:
        return sys.argv[idx]
    return os.environ.get(env_var, default)


async def main():
    team_id = get_arg_or_env(2, "TEAM_ID", "t24")
    user = get_arg_or_env(3, "USER", "Cline")
    backend_host = os.environ.get("BACKEND_HOST")
    if not backend_host:
        if len(sys.argv) > 1:
            backend_host = sys.argv[1]
        else:
            backend_host = "localhost:8000"
    # Set env vars for the tool
    os.environ["INTERNAL_CHAT_TEAM_ID"] = team_id
    os.environ["INTERNAL_CHAT_USER"] = user
    os.environ["BACKEND_HOST"] = backend_host
    print(
        f"--- Using backend_host: {backend_host} | team_id: {team_id} | user: {user} ---"
    )
    print("--- Sending test message ---")
    send_tool = SendMessageTool()
    send_input = SendMessageInput(
        message="Test message from test_get_unread_messages.py"
    )
    try:
        send_result = await send_tool.execute(send_input)
        print("SendMessageTool result:", send_result)
    except Exception as e:
        print("SendMessageTool error:", e)

    print(
        "--- Fetching unread messages with filters (should use POST /messages/query) ---"
    )
    get_tool = GetUnreadMessagesTool()
    get_input = GetUnreadMessagesInput(filters=MessageFilter(user=user, limit=10))
    try:
        get_result = await get_tool.execute(get_input)
        print("GetUnreadMessagesTool result:", get_result)
    except Exception as e:
        print("GetUnreadMessagesTool error:", e)


if __name__ == "__main__":
    asyncio.run(main())

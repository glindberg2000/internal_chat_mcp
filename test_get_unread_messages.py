import asyncio
from internal_chat_mcp.tools.send_message import SendMessageTool, SendMessageInput
from internal_chat_mcp.tools.get_unread_messages import (
    GetUnreadMessagesTool,
    GetUnreadMessagesInput,
    MessageFilter,
)


async def main():
    team_id = "t24"
    user = "Cline"
    backend_host = "localhost:8000"

    print("--- Sending test message ---")
    send_tool = SendMessageTool()
    send_input = SendMessageInput(
        team_id=team_id,
        user=user,
        message="Test message from test_get_unread_messages.py",
        backend_host=backend_host,
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
    get_input = GetUnreadMessagesInput(
        team_id=team_id,
        backend_host=backend_host,
        filters=MessageFilter(user=user, limit=10),
    )
    try:
        get_result = await get_tool.execute(get_input)
        print("GetUnreadMessagesTool result:", get_result)
    except Exception as e:
        print("GetUnreadMessagesTool error:", e)


if __name__ == "__main__":
    asyncio.run(main())

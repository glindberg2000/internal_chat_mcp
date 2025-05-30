from typing import Optional, Dict, Any
from pydantic import Field, BaseModel, ConfigDict
from ..interfaces.tool import Tool, BaseToolInput, ToolResponse
import asyncio
import websockets
import json
import os


class SendMessageInput(BaseToolInput):
    team_id: str = Field(..., description="Team ID to send the message to")
    user: str = Field(..., description="User sending the message")
    message: str = Field(..., description="Message content")
    backend_host: str = Field(
        "host.docker.internal:8000",
        description="Backend host and port (default: host.docker.internal:8000)",
    )
    reply_to_user: Optional[str] = Field(
        None,
        description="If set, automatically mention this user in the message if not already present.",
    )


class SendMessageOutput(BaseModel):
    status: str
    detail: Optional[str] = None


class SendMessageTool(Tool):
    name = "SendMessage"
    description = "Send a message to the internal team chat via WebSocket."
    input_model = SendMessageInput
    output_model = SendMessageOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: SendMessageInput) -> ToolResponse:
        # Always use BACKEND_HOST env var if set
        backend_host = os.environ.get("BACKEND_HOST", input_data.backend_host)
        # Use INTERNAL_CHAT_USER if user not provided
        user = input_data.user or os.environ.get("INTERNAL_CHAT_USER")
        # Auto-mention reply_to_user if set and not already mentioned
        message = input_data.message
        reply_to_user = input_data.reply_to_user or ""
        if reply_to_user:
            mention = f"@{reply_to_user}"
            if mention.lower() not in message.lower():
                message = f"{mention} {message}"
        print(f"[DEBUG] Sending user param in SendMessage: {user}")
        ws_url = f"ws://{backend_host}/ws/{input_data.team_id}"
        try:
            async with websockets.connect(ws_url) as websocket:
                await websocket.send(json.dumps({"user": user, "message": message}))
                # Optionally, wait for an echo or confirmation
                # response = await websocket.recv()
            output = SendMessageOutput(status="success")
        except Exception as e:
            output = SendMessageOutput(status="error", detail=str(e))
        return ToolResponse.from_model(output)

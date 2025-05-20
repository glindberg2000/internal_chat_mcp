from typing import Optional, Dict, Any, List, Union
from pydantic import Field, BaseModel, ConfigDict
from ..interfaces.tool import Tool, BaseToolInput, ToolResponse
import asyncio
import websockets
import json
import re
import os


class MessageFilter(BaseModel):
    user: Optional[str] = None
    channels: Optional[List[str]] = None
    dm_only: Optional[bool] = None
    mention_only: Optional[bool] = None
    content_regex: Optional[str] = None
    from_user: Optional[str] = None
    before: Optional[str] = None
    after: Optional[str] = None
    sort: Optional[str] = "asc"
    limit: Optional[int] = 20


class WaitForMessageInput(BaseToolInput):
    team_id: str = Field(..., description="Team ID to wait for a message in")
    backend_host: str = Field(
        "host.docker.internal:8000",
        description="Backend host and port (default: host.docker.internal:8000)",
    )
    from_user: Optional[str] = Field(
        None,
        description="Only wait for messages from this user (defaults to INTERNAL_CHAT_USER if not set)",
    )
    mention_only: Optional[bool] = Field(
        False,
        description="Only wait for messages that mention the user (INTERNAL_CHAT_USER)",
    )
    timeout: int = Field(
        default=30, description="Timeout in seconds to wait for a message"
    )


class WaitForMessageOutput(BaseModel):
    id: Optional[int] = None
    user: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None
    channel: Optional[str] = None
    status: str = Field(..., description="success or timeout")
    detail: Optional[str] = None


class WaitForMessageTool(Tool):
    name = "WaitForMessage"
    description = "Wait for a message matching criteria on the internal team chat (WebSocket). Supports advanced filters."
    input_model = WaitForMessageInput
    output_model = WaitForMessageOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: WaitForMessageInput) -> ToolResponse:
        ws_url = f"ws://{input_data.backend_host}/ws/{input_data.team_id}"
        # Determine user to filter by
        user_to_match = input_data.from_user or os.getenv("INTERNAL_CHAT_USER")
        mention_name = os.getenv("INTERNAL_CHAT_USER")
        try:
            async with websockets.connect(ws_url) as websocket:
                try:
                    while True:
                        msg_raw = await asyncio.wait_for(
                            websocket.recv(), timeout=input_data.timeout
                        )
                        msg = json.loads(msg_raw)
                        # Filter by user if set
                        if user_to_match and msg.get("user") != user_to_match:
                            continue
                        # Filter by mention if set
                        if input_data.mention_only and mention_name:
                            if mention_name not in msg.get("message", ""):
                                continue
                        output = WaitForMessageOutput(
                            id=None,
                            user=msg.get("user"),
                            message=msg.get("message"),
                            timestamp=None,
                            channel=msg.get("channel"),
                            status="success",
                        )
                        return ToolResponse.from_model(output)
                except asyncio.TimeoutError:
                    output = WaitForMessageOutput(
                        status="timeout", detail="No matching message received in time."
                    )
                    return ToolResponse.from_model(output)
        except Exception as e:
            output = WaitForMessageOutput(status="error", detail=str(e))
            return ToolResponse.from_model(output)

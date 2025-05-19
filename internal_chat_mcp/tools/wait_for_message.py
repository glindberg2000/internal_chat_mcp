from typing import Optional, Dict, Any
from pydantic import Field, BaseModel, ConfigDict
from ..interfaces.tool import Tool, BaseToolInput, ToolResponse
import asyncio
import websockets
import json
import re


class WaitForMessageInput(BaseToolInput):
    team_id: str = Field(..., description="Team ID to listen for messages")
    backend_host: str = Field(
        default="localhost:8000",
        description="Backend host and port (default: localhost:8000)",
    )
    sender: Optional[str] = Field(
        None, description="Only match messages from this user"
    )
    mention_only: Optional[bool] = Field(
        False, description="Only match messages containing '@'"
    )
    content_regex: Optional[str] = Field(
        None, description="Only match messages matching this regex"
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
    description = (
        "Wait for a message matching criteria on the internal team chat (WebSocket)."
    )
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
        try:
            async with websockets.connect(ws_url) as websocket:
                try:
                    while True:
                        msg_raw = await asyncio.wait_for(
                            websocket.recv(), timeout=input_data.timeout
                        )
                        msg = json.loads(msg_raw)
                        # Match sender
                        if input_data.sender and msg.get("user") != input_data.sender:
                            continue
                        # Match mention_only
                        if input_data.mention_only and "@" not in msg.get(
                            "message", ""
                        ):
                            continue
                        # Match content_regex
                        if input_data.content_regex and not re.search(
                            input_data.content_regex, msg.get("message", "")
                        ):
                            continue
                        output = WaitForMessageOutput(
                            id=None,  # Not available from WS, unless backend echoes
                            user=msg.get("user"),
                            message=msg.get("message"),
                            timestamp=None,  # Not available from WS, unless backend echoes
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

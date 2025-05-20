from typing import Optional, Dict, Any, List
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
    filters: Optional[MessageFilter] = Field(
        None, description="Advanced message filter (all fields optional)"
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
        filter = input_data.filters or MessageFilter()
        try:
            async with websockets.connect(ws_url) as websocket:
                try:
                    while True:
                        msg_raw = await asyncio.wait_for(
                            websocket.recv(), timeout=input_data.timeout
                        )
                        msg = json.loads(msg_raw)
                        # Apply filter fields
                        if filter.from_user and msg.get("user") != filter.from_user:
                            continue
                        if filter.mention_only and "@" not in msg.get("message", ""):
                            continue
                        if filter.content_regex and not re.search(
                            filter.content_regex, msg.get("message", "")
                        ):
                            continue
                        if (
                            filter.channels
                            and msg.get("channel", "general") not in filter.channels
                        ):
                            continue
                        if filter.dm_only and msg.get("channel") is not None:
                            continue
                        # Add more filter logic as needed
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

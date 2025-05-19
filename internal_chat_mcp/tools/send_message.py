from typing import Optional, Dict, Any
from pydantic import Field, BaseModel, ConfigDict
from ..interfaces.tool import Tool, BaseToolInput, ToolResponse
import asyncio
import websockets
import json


class SendMessageInput(BaseToolInput):
    team_id: str = Field(..., description="Team ID to send the message to")
    user: str = Field(..., description="User sending the message")
    message: str = Field(..., description="Message content")
    backend_host: str = Field(
        default="localhost:8000",
        description="Backend host and port (default: localhost:8000)",
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
        ws_url = f"ws://{input_data.backend_host}/ws/{input_data.team_id}"
        try:
            async with websockets.connect(ws_url) as websocket:
                await websocket.send(
                    json.dumps({"user": input_data.user, "message": input_data.message})
                )
                # Optionally, wait for an echo or confirmation
                # response = await websocket.recv()
            output = SendMessageOutput(status="success")
        except Exception as e:
            output = SendMessageOutput(status="error", detail=str(e))
        return ToolResponse.from_model(output)

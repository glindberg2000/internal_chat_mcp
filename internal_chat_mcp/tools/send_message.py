from typing import Optional, Dict, Any
from pydantic import Field, BaseModel, ConfigDict
from ..interfaces.tool import Tool, BaseToolInput, ToolResponse
import asyncio
import websockets
import json
import os
import logging


class SendMessageInput(BaseToolInput):
    message: str = Field(..., description="Message content")
    # NOTE for LLMs/clients: reply_to_user should be omitted if not used, or set to a string. Do NOT send null explicitly in JSON; if you must, null will be treated as not set.
    reply_to_user: Optional[str] = Field(
        default=None,
        description="(Optional) Username to mention in the message. Omit this field or set to a string. Do NOT send null explicitly; if null is sent, it will be treated as not set.",
    )


class SendMessageOutput(BaseModel):
    status: str
    detail: Optional[str] = None


class SendMessageTool(Tool):
    name = "SendMessage"
    description = "Send a message to the internal team chat via WebSocket. Team, user, and backend host are determined by the MCP config/environment."
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
        backend_host = os.environ["BACKEND_HOST"]
        user = os.environ["INTERNAL_CHAT_USER"]
        team_id = os.environ["INTERNAL_CHAT_TEAM_ID"]
        message = input_data.message
        reply_to_user = getattr(input_data, "reply_to_user", None)
        # Accept omitted, None, or string for reply_to_user. Treat null as not set.
        if reply_to_user is None or reply_to_user == "null":
            reply_to_user = ""
        elif not isinstance(reply_to_user, str):
            logging.error(
                f"[SendMessageTool] Invalid type for reply_to_user: {type(reply_to_user)}. Value: {reply_to_user}"
            )
            output = SendMessageOutput(
                status="error",
                detail="Invalid type for 'reply_to_user'. Must be a string or omitted.",
            )
            return ToolResponse.from_model(output)
        if reply_to_user:
            mention = f"@{reply_to_user}"
            if mention.lower() not in message.lower():
                message = f"{mention} {message}"
        logging.debug(f"[DEBUG] Sending user param in SendMessage: {user}")
        ws_url = f"ws://{backend_host}/ws/{team_id}"
        try:
            async with websockets.connect(ws_url) as websocket:
                await websocket.send(json.dumps({"user": user, "message": message}))
            output = SendMessageOutput(status="success")
        except Exception as e:
            output = SendMessageOutput(status="error", detail=str(e))
        return ToolResponse.from_model(output)

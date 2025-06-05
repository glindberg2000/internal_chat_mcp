from typing import Optional, Dict, Any, List, Union
from pydantic import Field, BaseModel, ConfigDict
from ..interfaces.tool import Tool, BaseToolInput, ToolResponse
import asyncio
import websockets
import json
import re
import os


def log_debug(msg):
    with open("/tmp/wait_for_message_debug.log", "a") as f:
        f.write(msg + "\n")


log_debug("[DEBUG] wait_for_message.py loaded")


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
    description = "Wait for a message matching criteria on the internal team chat (WebSocket). Team and backend host are determined by the MCP config/environment. Supports advanced filters."
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
        log_debug(f"[DEBUG] WaitForMessageTool.execute called with input: {input_data}")
        backend_host = os.environ["BACKEND_HOST"]
        team_id = os.environ["INTERNAL_CHAT_TEAM_ID"]
        from_user = input_data.from_user or os.environ.get("INTERNAL_CHAT_USER")
        mention_only = input_data.mention_only
        if isinstance(mention_only, str):
            mention_only = mention_only.lower() == "true"
        mention_user = os.environ.get("INTERNAL_CHAT_USER")
        mention_pattern = None
        if mention_only and mention_user:
            import re

            mention_pattern = re.compile(
                rf"(?:^|[^\\w])@{re.escape(mention_user)}(?:[^\\w]|$)", re.IGNORECASE
            )
            log_debug(f"[DEBUG] Using mention regex: {mention_pattern.pattern}")
        try:
            ws_url = f"ws://{backend_host}/ws/{team_id}"
            timeout = input_data.timeout
            async with websockets.connect(ws_url) as websocket:
                try:
                    while True:
                        msg_raw = await asyncio.wait_for(
                            websocket.recv(), timeout=timeout
                        )
                        msg = json.loads(msg_raw)
                        log_debug(f"[DEBUG] Received message: {msg}")
                        # Apply from_user filter if set
                        if from_user:
                            if msg.get("user") != from_user:
                                log_debug(
                                    f"[DEBUG] Skipping message from user: {msg.get('user')} (wanted: {from_user})"
                                )
                                continue
                        # Apply mention filter if set
                        if mention_pattern:
                            message_text = msg.get("message", "")
                            log_debug(
                                f"[DEBUG] Checking message for mention: {repr(message_text)}"
                            )
                            if not mention_pattern.search(message_text):
                                log_debug(
                                    f"[DEBUG] No mention match for user {mention_user}"
                                )
                                continue
                            else:
                                log_debug(
                                    f"[DEBUG] Mention match for user {mention_user}"
                                )
                        # If no filters or all filters pass, return the message
                        log_debug(f"[DEBUG] Accepting message: {msg}")
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
            log_debug(f"[DEBUG] Exception in WaitForMessageTool: {e}")
            output = WaitForMessageOutput(status="error", detail=str(e))
            return ToolResponse.from_model(output)

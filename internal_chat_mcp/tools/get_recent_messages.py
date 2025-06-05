from typing import Optional, List, Dict, Any
from pydantic import Field, BaseModel
from ..interfaces.tool import Tool, BaseToolInput, ToolResponse
import httpx
import os
import logging


class GetRecentMessagesInput(BaseToolInput):
    limit: Optional[int] = Field(20, description="Max number of messages to return")


class MessageModel(BaseModel):
    id: int
    user: str
    message: str
    timestamp: str
    channel: Optional[str] = None


class GetRecentMessagesOutput(BaseModel):
    messages: List[MessageModel]


class GetRecentMessagesTool(Tool):
    name = "GetRecentMessages"
    description = "Fetch the most recent messages for a team from the internal chat backend (REST). Team and backend host are determined by the MCP config/environment. Uses GET /api/team/<team>/messages?limit=N."
    input_model = GetRecentMessagesInput
    output_model = GetRecentMessagesOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: GetRecentMessagesInput) -> ToolResponse:
        backend_host = os.environ["BACKEND_HOST"]
        team_id = os.environ["INTERNAL_CHAT_TEAM_ID"]
        url = f"http://{backend_host}/api/team/{team_id}/messages"
        params = {"limit": input_data.limit or 20}
        logging.debug(f"[DEBUG] GetRecentMessagesTool GET {url} | params={params}")
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            logging.debug(
                f"[DEBUG] Response status: {resp.status_code}, body: {resp.text}"
            )
            resp.raise_for_status()
            data = resp.json()
            messages = [MessageModel(**m) for m in data.get("messages", [])]
            output = GetRecentMessagesOutput(messages=messages)
        return ToolResponse.from_model(output)

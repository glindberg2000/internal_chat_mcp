from typing import Optional, List, Dict, Any
from pydantic import Field, BaseModel, ConfigDict
from ..interfaces.tool import Tool, BaseToolInput, ToolResponse
import httpx


class GetUnreadMessagesInput(BaseToolInput):
    team_id: str = Field(..., description="Team ID to fetch messages for")
    backend_host: str = Field(
        default="localhost:8000",
        description="Backend host and port (default: localhost:8000)",
    )
    since_message_id: Optional[int] = Field(
        None, description="Only messages with id > since_message_id"
    )
    sender: Optional[str] = Field(None, description="Only messages from this user")
    limit: int = Field(default=20, description="Max number of messages to return")
    mention_only: Optional[bool] = Field(
        False, description="Only messages containing '@'"
    )
    dm_only: Optional[bool] = Field(
        False, description="Only messages with channel == None"
    )
    content_regex: Optional[str] = Field(
        None, description="Only messages matching this regex"
    )


class MessageModel(BaseModel):
    id: int
    user: str
    message: str
    timestamp: str
    channel: Optional[str] = None


class GetUnreadMessagesOutput(BaseModel):
    messages: List[MessageModel]


class GetUnreadMessagesTool(Tool):
    name = "GetUnreadMessages"
    description = (
        "Fetch unread messages for a team from the internal chat backend (REST)."
    )
    input_model = GetUnreadMessagesInput
    output_model = GetUnreadMessagesOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: GetUnreadMessagesInput) -> ToolResponse:
        url = f"http://{input_data.backend_host}/api/team/{input_data.team_id}/messages"
        params = {}
        if input_data.since_message_id is not None:
            params["since_message_id"] = input_data.since_message_id
        if input_data.sender:
            params["sender"] = input_data.sender
        if input_data.limit:
            params["limit"] = input_data.limit
        if input_data.mention_only:
            params["mention_only"] = str(input_data.mention_only).lower()
        if input_data.dm_only:
            params["dm_only"] = str(input_data.dm_only).lower()
        if input_data.content_regex:
            params["content_regex"] = input_data.content_regex
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            messages = [MessageModel(**m) for m in data.get("messages", [])]
            output = GetUnreadMessagesOutput(messages=messages)
        return ToolResponse.from_model(output)

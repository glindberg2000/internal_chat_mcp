from typing import Optional, List, Dict, Any
from pydantic import Field, BaseModel
from ..interfaces.tool import Tool, BaseToolInput, ToolResponse
import httpx
import os


class GetRecentMessagesInput(BaseToolInput):
    team_id: str = Field(..., description="Team ID to fetch messages for")
    backend_host: str = Field(
        "host.docker.internal:8000",
        description="Backend host and port (default: host.docker.internal:8000)",
    )
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
    description = "Fetch the most recent messages for a team from the internal chat backend (REST). Uses GET /api/team/<team>/messages?limit=N."
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
        backend_host = os.environ.get("BACKEND_HOST", input_data.backend_host)
        url = f"http://{backend_host}/api/team/{input_data.team_id}/messages"
        params = {"limit": input_data.limit or 20}
        print(f"[DEBUG] GetRecentMessagesTool GET {url} | params={params}")
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            print(f"[DEBUG] Response status: {resp.status_code}, body: {resp.text}")
            resp.raise_for_status()
            data = resp.json()
            messages = [MessageModel(**m) for m in data.get("messages", [])]
            output = GetRecentMessagesOutput(messages=messages)
        return ToolResponse.from_model(output)

from ..interfaces.tool import Tool, BaseToolInput, ToolResponse
from pydantic import BaseModel
import internal_chat_mcp
from typing import Dict, Any


class GetVersionOutput(BaseModel):
    version: str


class GetVersionTool(Tool):
    name = "GetVersion"
    description = "Return the current version of the internal_chat_mcp package. Useful for debugging and support."
    input_model = BaseToolInput
    output_model = GetVersionOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: BaseToolInput) -> ToolResponse:
        return ToolResponse.from_model(
            GetVersionOutput(version=internal_chat_mcp.__version__)
        )

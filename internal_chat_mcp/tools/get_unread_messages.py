from typing import Optional, List, Dict, Any
from pydantic import Field, BaseModel, ConfigDict
from ..interfaces.tool import Tool, BaseToolInput, ToolResponse
import httpx
import logging
import os


class MessageFilter(BaseModel):
    """
    MessageFilter for advanced chat message queries.
    Only use these fields inside the 'filters' object of GetUnreadMessagesInput.
    Example:
        filters = MessageFilter(user="Cline", limit=10)
    Fields:
        user: Only messages from this user
        channels: List of channel names/IDs
        dm_only: Only direct messages
        mention_only: Only messages mentioning the user
        content_regex: Only messages matching this regex
        from_user: (legacy/alias) Only messages from this user
        before/after: Message ID or timestamp range
        sort: 'asc' or 'desc'
        limit: Max number of messages
    """

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


class GetUnreadMessagesInput(BaseToolInput):
    """
    Input for GetUnreadMessagesTool. Only use the fields defined here.
    Example (fetch last 10 messages from user 'Cline'):
        {
            "filters": {"user": "Cline", "limit": 10}
        }
    Example (fetch last 5 messages mentioning you):
        {
            "mention_only": true,
            "limit": 5
        }
    Do NOT use 'from_user' at the top level. Place it inside 'filters' if needed.
    """

    filters: Optional[MessageFilter] = Field(
        None, description="Advanced message filter (all fields optional)"
    )
    since_message_id: Optional[int] = Field(
        None, description="Only messages with id > since_message_id"
    )
    limit: Optional[int] = Field(
        default=20, description="Max number of messages to return"
    )
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
        "Fetch unread messages for a team from the internal chat backend (REST). "
        "Team, user, and backend host are determined by the MCP config/environment. "
        "Supports advanced filters via POST /messages/query.\n"
        "\nUSAGE EXAMPLES:\n"
        '- {"filters": {"user": "Cline", "limit": 10}}\n'
        '- {"mention_only": true, "limit": 5}\n'
        "\nDo NOT use 'from_user' at the top level. Place it inside 'filters' if needed."
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

    def coerce_bool(self, val):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() == "true"
        return False

    def coerce_int(self, val):
        if isinstance(val, int):
            return val
        if isinstance(val, str) and val.isdigit():
            return int(val)
        return None

    async def execute(self, input_data: GetUnreadMessagesInput) -> ToolResponse:
        backend_host = os.environ["BACKEND_HOST"]
        team_id = os.environ["INTERNAL_CHAT_TEAM_ID"]
        user = os.environ["INTERNAL_CHAT_USER"]
        url = f"http://{backend_host}/api/team/{team_id}/messages"
        # Always use POST /messages/query if filters are provided
        if input_data.filters:
            # If filters is a string (bad agent), try to parse it
            if isinstance(input_data.filters, str):
                import json as _json

                try:
                    filters_obj = MessageFilter(**_json.loads(input_data.filters))
                except Exception:
                    filters_obj = MessageFilter()
            else:
                filters_obj = input_data.filters
            # Ensure user is included in filters if sender is present
            # if input_data.from_user and not filters_obj.user:
            #     filters_obj.user = input_data.from_user
            # If still no user, use env var
            if not filters_obj.user:
                filters_obj.user = user
            logging.debug(f"[DEBUG] Sending user param in filters: {filters_obj.user}")
            query_url = f"{url}/query"
            payload = filters_obj.model_dump()
            logging.debug(f"[DEBUG] POST {query_url} | payload={payload}")
            async with httpx.AsyncClient() as client:
                resp = await client.post(query_url, json=payload)
                logging.debug(
                    f"[DEBUG] Response status: {resp.status_code}, body: {resp.text}"
                )
                resp.raise_for_status()
                data = resp.json()
                messages = [MessageModel(**m) for m in data.get("messages", [])]
                output = GetUnreadMessagesOutput(messages=messages)
            return ToolResponse.from_model(output)
        else:
            params = {}
            # Only filter by user if provided
            user_param = None
            # if input_data.from_user:
            #     user_param = input_data.from_user
            if input_data.filters and getattr(input_data.filters, "user", None):
                user_param = input_data.filters.user
            # If still no user, use env var
            if not user_param:
                user_param = user
            logging.debug(f"[DEBUG] Sending user param in GET: {user_param}")
            if user_param:
                params["user"] = user_param
            # If no user param, do not raise an error—fetch all unread messages for the team/channel
            if input_data.since_message_id is not None:
                params["since_message_id"] = self.coerce_int(
                    input_data.since_message_id
                )
            if input_data.limit is not None:
                params["limit"] = self.coerce_int(input_data.limit)
            if input_data.mention_only is not None:
                params["mention_only"] = str(
                    self.coerce_bool(input_data.mention_only)
                ).lower()
            if input_data.dm_only is not None:
                params["dm_only"] = str(self.coerce_bool(input_data.dm_only)).lower()
            if input_data.content_regex:
                params["content_regex"] = input_data.content_regex
            logging.debug(f"[DEBUG] GET {url} | params={params}")
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params)
                logging.debug(
                    f"[DEBUG] Response status: {resp.status_code}, body: {resp.text}"
                )
                resp.raise_for_status()
                data = resp.json()
                messages = [MessageModel(**m) for m in data.get("messages", [])]
                output = GetUnreadMessagesOutput(messages=messages)
            return ToolResponse.from_model(output)

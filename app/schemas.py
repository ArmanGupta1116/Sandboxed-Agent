from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    task: str = Field(
        min_length=1,
        max_length=2000,
    )


class ToolRequest(BaseModel):
    name: str
    arguments: dict


class ToolResult(BaseModel):
    success: bool
    output: str
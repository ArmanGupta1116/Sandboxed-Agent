from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class TaskMessage(BaseModel):
    task_id: str
    task: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class AgentEvent(BaseModel):
    event_id: str
    task_id: str
    event_type: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    payload: dict[str, Any] = Field(default_factory=dict)
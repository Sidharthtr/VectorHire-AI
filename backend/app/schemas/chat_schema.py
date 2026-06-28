"""
Pydantic payloads for the per-analysis chat feature.

What it does:
- ChatRequest: incoming user message (length-validated, 1..4000 chars).
- ChatMessageOut: serialised ChatMessage row sent back to the UI, including timestamp.
- `from_attributes=True` lets FastAPI build ChatMessageOut directly from an ORM row.

Upstream (who imports this): app.api.routes.analysis_routes (chat send + history endpoints).
Downstream (what this imports): datetime (for created_at), pydantic (BaseModel, Field, ConfigDict).
"""
from __future__ import annotations
# datetime: type for the created_at timestamp echoed back to the client
from datetime import datetime
# BaseModel/Field/ConfigDict: define request+response models with length limits and ORM-mode
from pydantic import BaseModel, Field, ConfigDict


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    created_at: datetime


class ChatRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)

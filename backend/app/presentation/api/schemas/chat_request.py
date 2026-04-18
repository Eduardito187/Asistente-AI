from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    mensaje: str
    sesion_id: Optional[UUID] = None

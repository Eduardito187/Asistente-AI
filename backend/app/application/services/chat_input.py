from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class ChatInput:
    """DTO de entrada del caso de uso ProcesarChat."""

    mensaje: str
    sesion_id: Optional[UUID] = None

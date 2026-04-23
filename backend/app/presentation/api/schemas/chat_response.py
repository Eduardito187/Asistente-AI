from __future__ import annotations

from typing import List
from uuid import UUID

from pydantic import BaseModel

from .producto import ProductoOut


class ChatResponse(BaseModel):
    sesion_id: UUID
    respuesta: str
    productos_citados: List[ProductoOut] = []
    productos_sugeridos: List[ProductoOut] = []
    pasos: List[dict] = []

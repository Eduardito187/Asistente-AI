from __future__ import annotations

from pydantic import BaseModel


class OrdenResumen(BaseModel):
    numero_orden: str
    cliente_nombre: str
    total_bob: float
    items_cantidad: int
    estado: str
    created_at: str

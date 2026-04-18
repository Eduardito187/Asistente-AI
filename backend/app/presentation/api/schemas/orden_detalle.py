from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from .orden_detalle_item import OrdenDetalleItem


class OrdenDetalle(BaseModel):
    numero_orden: str
    sesion_id: UUID
    cliente_nombre: str
    cliente_email: Optional[str]
    cliente_telefono: Optional[str]
    cliente_ciudad: str
    total_bob: float
    items_cantidad: int
    estado: str
    notas: Optional[str]
    created_at: str
    items: List[OrdenDetalleItem]

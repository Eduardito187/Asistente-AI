from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class OrdenDetalleItem(BaseModel):
    sku: str
    nombre: str
    marca: Optional[str]
    cantidad: int
    precio_unitario_bob: float
    subtotal_bob: float

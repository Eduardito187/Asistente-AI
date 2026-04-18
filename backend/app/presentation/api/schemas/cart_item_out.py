from __future__ import annotations

from pydantic import BaseModel


class CartItemOut(BaseModel):
    sku: str
    nombre: str
    cantidad: int
    precio_unitario_bob: float
    subtotal_bob: float

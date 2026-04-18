from __future__ import annotations

from pydantic import BaseModel


class CartItemIn(BaseModel):
    sku: str
    cantidad: int = 1

from __future__ import annotations

from typing import List
from uuid import UUID

from pydantic import BaseModel

from .cart_item_out import CartItemOut


class CartView(BaseModel):
    sesion_id: UUID
    items: List[CartItemOut]
    total_bob: float

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..productos import SKU, PrecioBob
from ..shared.errors import ReglaDeNegocioViolada


@dataclass
class OrdenItem:
    """Entity hija del agregado Orden."""

    sku: SKU
    nombre: str
    marca: Optional[str]
    cantidad: int
    precio_unitario: PrecioBob

    def __post_init__(self) -> None:
        if self.cantidad < 1:
            raise ReglaDeNegocioViolada("cantidad de item no puede ser menor a 1")

    @property
    def subtotal_bob(self) -> float:
        return round(self.cantidad * self.precio_unitario.monto, 2)

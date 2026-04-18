from __future__ import annotations

from dataclasses import dataclass

from ..productos import SKU, PrecioBob
from ..shared.errors import ReglaDeNegocioViolada


@dataclass
class CarritoItem:
    """Entity hija del agregado Carrito."""

    sku: SKU
    nombre: str
    cantidad: int
    precio_unitario: PrecioBob

    def __post_init__(self) -> None:
        if self.cantidad < 1:
            raise ReglaDeNegocioViolada("cantidad minima en carrito es 1")

    @property
    def subtotal_bob(self) -> float:
        return round(self.cantidad * self.precio_unitario.monto, 2)

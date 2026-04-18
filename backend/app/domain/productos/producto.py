from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .precio_bob import PrecioBob
from .sku import SKU


@dataclass(frozen=True)
class Producto:
    """Agregado de lectura del catálogo. El ingestor escribe, el backend lee."""

    sku: SKU
    nombre: str
    descripcion: Optional[str]
    categoria: Optional[str]
    subcategoria: Optional[str]
    marca: Optional[str]
    precio: PrecioBob
    precio_anterior: Optional[PrecioBob]
    stock: int
    imagen_url: Optional[str]
    activo: bool

    def disponible(self) -> bool:
        return self.activo and self.stock > 0

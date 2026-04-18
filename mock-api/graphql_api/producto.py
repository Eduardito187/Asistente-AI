from __future__ import annotations

from typing import Optional

import strawberry


@strawberry.type
class Producto:
    sku: str
    nombre: str
    descripcion: Optional[str]
    categoria: Optional[str]
    marca: Optional[str]
    precio_bob: float
    precio_anterior_bob: Optional[float]
    stock: int
    imagen_url: Optional[str]
    activo: bool

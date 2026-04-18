from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ProductoOut(BaseModel):
    """Representación HTTP de un Producto del catálogo."""

    sku: str
    nombre: str
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    subcategoria: Optional[str] = None
    marca: Optional[str] = None
    precio_bob: float
    precio_anterior_bob: Optional[float] = None
    stock: int
    imagen_url: Optional[str] = None
    activo: bool = True

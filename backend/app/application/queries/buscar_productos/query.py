from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BuscarProductosQuery:
    """Query: busqueda de productos con filtros de catalogo."""

    query: Optional[str] = None
    categoria: Optional[str] = None
    subcategoria: Optional[str] = None
    marca: Optional[str] = None
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None
    solo_con_stock: bool = True
    limite: int = 6

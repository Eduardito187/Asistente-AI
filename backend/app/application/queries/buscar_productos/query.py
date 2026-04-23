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
    pulgadas: Optional[float] = None
    pulgadas_min: Optional[float] = None
    pulgadas_max: Optional[float] = None
    capacidad_gb_min: Optional[int] = None
    ram_gb_min: Optional[int] = None
    capacidad_litros_min: Optional[float] = None
    capacidad_kg_min: Optional[float] = None
    potencia_w_min: Optional[int] = None
    potencia_w_max: Optional[int] = None
    procesador: Optional[str] = None
    tipo_panel: Optional[str] = None
    resolucion: Optional[str] = None
    color: Optional[str] = None
    es_electrico: Optional[bool] = None
    solo_con_stock: bool = True
    limite: int = 6
    excluir_accesorios: bool = False
    solo_accesorios: bool = False
    excluir_skus: Optional[tuple[str, ...]] = None
    genero: Optional[str] = None
    nombre_excluye: Optional[tuple[str, ...]] = None

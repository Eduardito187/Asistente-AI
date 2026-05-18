from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoberturaAtributosQuery:
    """Query: porcentaje de productos con cada columna estructurada poblada."""
    por_categoria: bool = False

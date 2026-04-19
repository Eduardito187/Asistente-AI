from __future__ import annotations

from dataclasses import dataclass, field

from ....domain.productos import Producto


@dataclass
class ResultadoCompararProductos:
    """DTO del comparador: productos encontrados + SKUs no encontrados."""

    productos: list[Producto] = field(default_factory=list)
    skus_no_encontrados: list[str] = field(default_factory=list)

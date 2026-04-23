from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ....domain.productos import Producto


@dataclass
class ResultadoCompararProductos:
    """DTO del comparador: productos encontrados + SKUs no encontrados +
    tabla comparativa estructurada con conclusión (mejor general, mejor
    precio-calidad, más económica). La tabla y conclusión las genera el
    servicio ComparadorProductos de forma determinista."""

    productos: list[Producto] = field(default_factory=list)
    skus_no_encontrados: list[str] = field(default_factory=list)
    tabla: Optional[dict] = None
    conclusion: Optional[dict] = None

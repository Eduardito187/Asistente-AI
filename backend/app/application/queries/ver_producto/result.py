from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ....domain.productos import Producto


@dataclass
class ResultadoVerProducto:
    """DTO de salida de VerProductoHandler: producto o sugerencias similares."""

    producto: Optional[Producto]
    skus_similares: list[str]

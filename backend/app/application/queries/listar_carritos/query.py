from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ....domain.sesiones import EstadoCarrito


@dataclass(frozen=True)
class ListarCarritosQuery:
    """Query: listado admin de carritos con filtros de estado y contenido."""

    estado: Optional[EstadoCarrito] = None
    solo_con_items: bool = False
    limite: int = 100

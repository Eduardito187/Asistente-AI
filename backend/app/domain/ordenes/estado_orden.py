from __future__ import annotations

from enum import Enum


class EstadoOrden(str, Enum):
    """Ciclo de vida de una Orden."""

    CONFIRMADA = "confirmada"
    ENVIADA = "enviada"
    ENTREGADA = "entregada"
    CANCELADA = "cancelada"

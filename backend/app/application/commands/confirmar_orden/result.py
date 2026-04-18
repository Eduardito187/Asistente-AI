from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ResultadoConfirmarOrden:
    """DTO de salida de ConfirmarOrdenHandler."""

    numero_orden: str
    orden_id: str
    total_bob: float
    items_cantidad: int
    cliente_nombre: str
    cliente_email: Optional[str]
    cliente_telefono: Optional[str]

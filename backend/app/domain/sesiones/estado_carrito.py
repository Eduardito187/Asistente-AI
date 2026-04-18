from __future__ import annotations

from enum import Enum


class EstadoCarrito(str, Enum):
    """Ciclo de vida del carrito asociado a una Sesion."""

    ACTIVO = "activo"
    ABANDONADO = "abandonado"
    CONVERTIDO = "convertido"

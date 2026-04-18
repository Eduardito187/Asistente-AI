from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResultadoAgregar:
    """DTO de salida de AgregarAlCarritoHandler."""

    sku: str
    nombre: str
    cantidad_agregada: int
    precio_unitario_bob: float

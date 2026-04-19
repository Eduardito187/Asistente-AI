from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ResultadoValidacionProducto:
    """Respuesta del `ValidadorProductoReal`: si el concepto pedido es un producto
    real (p.ej. "iPhone 15 Pro Max") o un invento/galimatías del cliente."""

    es_real: bool
    nombre_canonico: Optional[str]
    categoria: Optional[str]
    marca: Optional[str]

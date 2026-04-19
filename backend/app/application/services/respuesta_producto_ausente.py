from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class RespuestaProductoAusente:
    """Resultado del `ManejadorProductoAusente`: texto para el cliente y
    alternativas reales a mostrar."""

    texto: str
    productos_alternativos: List[dict]
    skus_alternativos: List[str]
    sugerencia_registrada: bool

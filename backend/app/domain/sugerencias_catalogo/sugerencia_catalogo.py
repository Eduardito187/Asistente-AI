from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SugerenciaCatalogo:
    """Raíz del agregado SugerenciaCatalogo: un producto real pedido por un cliente
    que aún no está en el catálogo. SRP: modelar la pieza de vocabulario que el
    equipo comercial usará para priorizar altas de catálogo."""

    id: Optional[int]
    nombre: str
    nombre_norm: str
    categoria_estimada: Optional[str]
    marca_estimada: Optional[str]
    veces_solicitado: int
    primer_contexto_cliente: Optional[str]
    primera_fecha: datetime
    ultima_fecha: datetime

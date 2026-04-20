from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CategoriaRelacionada:
    """Relacion entre una categoria pedida (puede no existir, ej. 'autos') y
    una categoria real a ofrecer como fallback (ej. 'Automotriz/Vehiculos' =
    motocicletas). SRP: evitar que el agente niegue categorias que si tenemos."""

    categoria_origen: str
    categoria_sugerida: str
    subcategoria_sugerida: Optional[str]
    razon: str
    prioridad: int

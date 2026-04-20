from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FiltrosAtributos:
    """VO inmutable con filtros sobre atributos estructurados del producto."""

    pulgadas: Optional[float] = None
    pulgadas_min: Optional[float] = None
    pulgadas_max: Optional[float] = None
    capacidad_gb_min: Optional[int] = None
    ram_gb_min: Optional[int] = None
    capacidad_litros_min: Optional[float] = None
    capacidad_kg_min: Optional[float] = None
    potencia_w_min: Optional[int] = None
    potencia_w_max: Optional[int] = None
    procesador: Optional[str] = None
    tipo_panel: Optional[str] = None
    resolucion: Optional[str] = None
    color: Optional[str] = None
    es_electrico: Optional[bool] = None

    def vacio(self) -> bool:
        return all(getattr(self, f) is None for f in self.__dataclass_fields__)

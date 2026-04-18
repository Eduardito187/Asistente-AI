from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResultadoIngesta:
    origen: str
    procesados: int
    rechazados: int
    desactivados: int

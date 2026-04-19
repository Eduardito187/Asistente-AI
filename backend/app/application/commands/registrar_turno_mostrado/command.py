from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from uuid import UUID


@dataclass(frozen=True)
class RegistrarTurnoMostradoCommand:
    """Comando: registra que un set de SKUs fue mostrado al cliente en este
    turno y cual fue el rango de precios visible. Se usa para anclar
    consultas relativas como 'mas barato' o 'uno mejor'."""

    sesion_id: UUID
    skus: Tuple[str, ...]
    precios: Tuple[float, ...]

    def tiene_datos(self) -> bool:
        return bool(self.skus)

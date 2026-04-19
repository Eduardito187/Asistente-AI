from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class CurarConversacionCommand:
    """Comando: crea o actualiza un ejemplo curado de conversacion."""

    sesion_id: Optional[UUID]
    etiqueta: Optional[str]
    cliente_texto: str
    asistente_texto: str
    score: int
    turnos: int
    llevo_a_orden: bool
    activa: bool = True

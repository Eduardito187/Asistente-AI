from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class RegistrarFeedbackTurnoCommand:
    """Comando: voto thumbs up/down sobre un turno especifico."""

    sesion_id: UUID
    turno_index: int
    voto: str  # "up" | "down"
    mensaje_usuario: Optional[str] = None
    respuesta_agente: Optional[str] = None
    comentario: Optional[str] = None

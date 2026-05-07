from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class VotoFeedback(str, Enum):
    POSITIVO = "up"
    NEGATIVO = "down"


@dataclass(frozen=True)
class FeedbackTurno:
    """Voto explicito del cliente sobre un turno especifico. Senial fuerte
    para training: thumbs up convierte a few-shot, thumbs down desactiva
    el ejemplo o lo manda a revision."""

    id: Optional[int]
    sesion_id: UUID
    turno_index: int
    mensaje_usuario: Optional[str]
    respuesta_agente: Optional[str]
    voto: VotoFeedback
    comentario: Optional[str]
    creado_en: datetime

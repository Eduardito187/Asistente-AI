from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class GoldenConversation:
    """Ejemplo perfecto, manualmente curado, con prioridad sobre auto-curados.
    Se inyecta SIEMPRE como few-shot relevante a su categoria/intencion.
    No se desactiva por feedback (es ground truth)."""

    id: Optional[int]
    caso_que_cubre: str
    categoria: Optional[str]
    intencion: Optional[str]
    uso: Optional[str]
    cliente_texto: str
    asistente_texto: str
    prioridad: int
    activo: bool
    errores_que_previene: list[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

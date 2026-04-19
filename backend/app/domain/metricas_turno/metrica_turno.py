from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class MetricaTurno:
    """Metricas de un turno de conversacion. SRP: modelar los numeros que
    necesitamos para medir latencia y calidad."""

    id: Optional[int]
    sesion_id: UUID
    mensaje_usuario_len: int
    respuesta_len: int
    tool_calls: int
    mentiras_detectadas: int
    productos_citados: int
    ruta: str
    tiempo_ms: int
    created_at: datetime

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RegistrarMetricaTurnoCommand:
    """Comando: registra metrica de un turno de chat."""

    sesion_id: UUID
    mensaje_usuario_len: int
    respuesta_len: int
    tool_calls: int
    mentiras_detectadas: int
    productos_citados: int
    ruta: str
    tiempo_ms: int

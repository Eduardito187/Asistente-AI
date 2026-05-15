from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
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
    prompt_version: Optional[str] = None
    quality_score: Optional[int] = None
    reason_code: Optional[str] = None
    variant_name: Optional[str] = None
    busquedas_sin_resultado: bool = False

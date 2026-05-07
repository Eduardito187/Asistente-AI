from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ConversacionFallida:
    """Agregado de auditoria: turnos donde el agente cayo al fallback canned
    o al sintetizador de trace. Sirve para failure-mining del agente."""

    id: Optional[int]
    sesion_id: Optional[UUID]
    mensaje_usuario: str
    perfil_estado: dict
    ultimo_buscar_args: Optional[dict]
    razon_fallo: str
    trace_resumen: Optional[str]
    creado_en: datetime

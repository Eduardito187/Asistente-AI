from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class RegistrarConversacionFallidaCommand:
    """Comando: persiste un turno fallido para failure-mining posterior."""

    sesion_id: Optional[UUID]
    mensaje_usuario: str
    perfil_estado: dict
    ultimo_buscar_args: Optional[dict]
    razon_fallo: str
    trace_resumen: Optional[str] = None

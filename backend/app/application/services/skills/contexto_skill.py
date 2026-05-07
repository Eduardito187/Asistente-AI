from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ContextoSkill:
    """Información que un Skill recibe para decidir si se activa y qué
    contribuir al turno. Inmutable y completa: el skill no necesita
    consultar nada más para decidir.

    `perfil` y `historial_user` se pasan ya leídos por el orquestador
    una vez, así múltiples skills no hacen N consultas a la BD."""

    mensaje: str
    sesion_id: UUID
    perfil: Any                  # ResultadoObtenerPerfilSesion (Any para evitar import ciclo)
    historial_user: list[str]    # mensajes user previos en orden cronológico
    ahora: datetime              # momento del turno (para skills temporales)

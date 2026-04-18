from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from .rol_mensaje import RolMensaje


@dataclass
class Mensaje:
    """Entidad: un turno de la conversación asociado a una Sesion."""

    sesion_id: UUID
    rol: RolMensaje
    contenido: str
    created_at: Optional[datetime] = None

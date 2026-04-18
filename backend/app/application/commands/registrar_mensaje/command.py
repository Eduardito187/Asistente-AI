from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ....domain.chat import RolMensaje


@dataclass(frozen=True)
class RegistrarMensajeCommand:
    """Comando: persistir un mensaje de chat en una sesion."""

    sesion_id: UUID
    rol: RolMensaje
    contenido: str

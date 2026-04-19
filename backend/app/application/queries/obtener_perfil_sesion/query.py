from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ObtenerPerfilSesionQuery:
    """Query: trae el perfil (preferencias declaradas) de la sesion."""

    sesion_id: UUID

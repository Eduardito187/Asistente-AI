from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CrearSesionCommand:
    """Comando de creacion de sesion nueva (sin parametros, id se genera)."""

    pass

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..shared.errors import ValorInvalido


@dataclass(frozen=True)
class DatosCliente:
    """Value Object con los datos del cliente al confirmar una orden."""

    nombre: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    ciudad: str = "Santa Cruz"

    def __post_init__(self) -> None:
        nombre = (self.nombre or "").strip()
        if not nombre:
            raise ValorInvalido("el nombre del cliente es obligatorio")
        object.__setattr__(self, "nombre", nombre)

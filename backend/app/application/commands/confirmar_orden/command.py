from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ConfirmarOrdenCommand:
    """Comando: convertir el carrito en orden confirmada con datos del cliente."""

    sesion_id: UUID
    cliente_nombre: str
    cliente_email: Optional[str] = None
    cliente_telefono: Optional[str] = None
    notas: Optional[str] = None

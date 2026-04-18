from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from .estado_carrito import EstadoCarrito


@dataclass
class Sesion:
    """Raíz del agregado Sesion (con su ciclo de carrito)."""

    id: UUID
    estado: EstadoCarrito
    cliente_nombre: Optional[str]
    cliente_email: Optional[str]
    cliente_telefono: Optional[str]
    ultima_actividad_at: datetime
    created_at: datetime

    @staticmethod
    def nueva() -> "Sesion":
        ahora = datetime.utcnow()
        return Sesion(
            id=uuid4(),
            estado=EstadoCarrito.ACTIVO,
            cliente_nombre=None,
            cliente_email=None,
            cliente_telefono=None,
            ultima_actividad_at=ahora,
            created_at=ahora,
        )

    def tocar(self) -> None:
        self.ultima_actividad_at = datetime.utcnow()

    def marcar_convertida(self, nombre: str, email: Optional[str], telefono: Optional[str]) -> None:
        self.estado = EstadoCarrito.CONVERTIDO
        self.cliente_nombre = nombre
        if email:
            self.cliente_email = email
        if telefono:
            self.cliente_telefono = telefono
        self.tocar()

    def marcar_abandonada(self) -> None:
        self.estado = EstadoCarrito.ABANDONADO

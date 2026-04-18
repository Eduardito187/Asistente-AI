from __future__ import annotations

from uuid import UUID

from .....domain.sesiones import EstadoCarrito, Sesion


class SesionMapper:
    """Materializa una Sesion desde un row crudo de MariaDB."""

    @staticmethod
    def from_row(r: dict) -> Sesion:
        return Sesion(
            id=UUID(r["id"]),
            estado=EstadoCarrito(r["carrito_estado"]),
            cliente_nombre=r.get("cliente_nombre"),
            cliente_email=r.get("cliente_email"),
            cliente_telefono=r.get("cliente_telefono"),
            ultima_actividad_at=r["ultima_actividad_at"],
            created_at=r["created_at"],
        )

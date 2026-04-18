from __future__ import annotations

from uuid import UUID

from .....domain.ordenes import DatosCliente, EstadoOrden, Orden, OrdenItem


class OrdenMapper:
    """Materializa una Orden desde un row crudo + items ya mapeados."""

    @staticmethod
    def from_row(r: dict, items: list[OrdenItem]) -> Orden:
        cliente = DatosCliente(
            nombre=r["cliente_nombre"],
            email=r.get("cliente_email"),
            telefono=r.get("cliente_telefono"),
            ciudad=r.get("cliente_ciudad") or "Santa Cruz",
        )
        return Orden(
            id=UUID(r["id"]),
            numero_orden=r["numero_orden"],
            sesion_id=UUID(r["sesion_id"]),
            cliente=cliente,
            items=items,
            estado=EstadoOrden(r["estado"]),
            notas=r.get("notas"),
            created_at=r.get("created_at"),
        )

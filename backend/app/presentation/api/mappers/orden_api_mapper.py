from __future__ import annotations

from ....domain.ordenes import Orden
from ..schemas import OrdenDetalle, OrdenDetalleItem, OrdenResumen


class OrdenApiMapper:
    """Convierte Ordenes de dominio a DTOs Pydantic de la API."""

    @staticmethod
    def resumen(o: Orden) -> OrdenResumen:
        return OrdenResumen(
            numero_orden=o.numero_orden or "",
            cliente_nombre=o.cliente.nombre,
            total_bob=o.total_bob,
            items_cantidad=o.items_cantidad,
            estado=o.estado.value,
            created_at=o.created_at.isoformat() if o.created_at else "",
        )

    @staticmethod
    def detalle(o: Orden) -> OrdenDetalle:
        return OrdenDetalle(
            numero_orden=o.numero_orden or "",
            sesion_id=o.sesion_id,
            cliente_nombre=o.cliente.nombre,
            cliente_email=o.cliente.email,
            cliente_telefono=o.cliente.telefono,
            cliente_ciudad=o.cliente.ciudad,
            total_bob=o.total_bob,
            items_cantidad=o.items_cantidad,
            estado=o.estado.value,
            notas=o.notas,
            created_at=o.created_at.isoformat() if o.created_at else "",
            items=[
                OrdenDetalleItem(
                    sku=str(i.sku),
                    nombre=i.nombre,
                    marca=i.marca,
                    cantidad=i.cantidad,
                    precio_unitario_bob=i.precio_unitario.monto,
                    subtotal_bob=i.subtotal_bob,
                )
                for i in o.items
            ],
        )

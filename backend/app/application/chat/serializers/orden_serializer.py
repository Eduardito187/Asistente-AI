from __future__ import annotations

from ....domain.ordenes import Orden


class OrdenSerializer:
    """Proyeccion JSON-friendly de una Orden para respuesta al LLM."""

    @staticmethod
    def a_dict(o: Orden) -> dict:
        return {
            "numero_orden": o.numero_orden,
            "cliente": o.cliente.nombre,
            "total_bob": o.total_bob,
            "items": o.items_cantidad,
            "estado": o.estado.value,
            "fecha": o.created_at.isoformat() if o.created_at else None,
        }

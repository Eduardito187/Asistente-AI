from __future__ import annotations

from ....domain.carritos import Carrito


class CarritoSerializer:
    """Proyeccion JSON-friendly del Carrito para respuesta al LLM."""

    @staticmethod
    def a_dict(c: Carrito) -> dict:
        return {
            "items": [
                {
                    "sku": str(i.sku),
                    "nombre": i.nombre,
                    "cantidad": i.cantidad,
                    "precio_unitario_bob": i.precio_unitario.monto,
                    "subtotal_bob": i.subtotal_bob,
                }
                for i in c.items
            ],
            "total_bob": c.total_bob,
        }

from __future__ import annotations

from ....domain.productos import Producto


class ComparacionSerializer:
    """Proyeccion lado-a-lado para el LLM: filas = campo, columnas = SKU."""

    CAMPOS = (
        ("sku", "SKU"),
        ("nombre", "Nombre"),
        ("marca", "Marca"),
        ("categoria", "Categoria"),
        ("precio_bob", "Precio (Bs)"),
        ("precio_anterior_bob", "Precio anterior (Bs)"),
    )

    @classmethod
    def a_dict(cls, productos: list[Producto]) -> dict:
        columnas = [cls._columna(p) for p in productos]
        filas = []
        for clave, titulo in cls.CAMPOS:
            filas.append(
                {
                    "campo": titulo,
                    "valores": [col.get(clave) for col in columnas],
                }
            )
        filas.append(
            {
                "campo": "Descripcion",
                "valores": [p.descripcion or "" for p in productos],
            }
        )
        return {
            "skus": [str(p.sku) for p in productos],
            "filas": filas,
        }

    @staticmethod
    def _columna(p: Producto) -> dict:
        return {
            "sku": str(p.sku),
            "nombre": p.nombre,
            "marca": p.marca or "",
            "categoria": p.categoria or "",
            "precio_bob": float(p.precio.monto),
            "precio_anterior_bob": float(p.precio_anterior.monto) if p.precio_anterior else None,
        }

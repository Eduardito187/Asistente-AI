from __future__ import annotations

from .....domain.productos import SKU, PrecioBob, Producto


class ProductoMapper:
    """Materializa un Producto desde un row crudo de MariaDB."""

    @staticmethod
    def from_row(r: dict) -> Producto:
        return Producto(
            sku=SKU(r["sku"]),
            nombre=r["nombre"],
            descripcion=r.get("descripcion"),
            categoria=r.get("categoria"),
            subcategoria=r.get("subcategoria"),
            marca=r.get("marca"),
            precio=PrecioBob(float(r["precio_bob"])),
            precio_anterior=(
                PrecioBob(float(r["precio_anterior_bob"]))
                if r.get("precio_anterior_bob") is not None
                else None
            ),
            stock=int(r.get("stock") or 0),
            imagen_url=r.get("imagen_url"),
            activo=bool(r.get("activo")),
            pulgadas=float(r["pulgadas"]) if r.get("pulgadas") is not None else None,
            capacidad_gb=int(r["capacidad_gb"]) if r.get("capacidad_gb") is not None else None,
            ram_gb=int(r["ram_gb"]) if r.get("ram_gb") is not None else None,
            capacidad_litros=float(r["capacidad_litros"]) if r.get("capacidad_litros") is not None else None,
            capacidad_kg=float(r["capacidad_kg"]) if r.get("capacidad_kg") is not None else None,
            potencia_w=int(r["potencia_w"]) if r.get("potencia_w") is not None else None,
            procesador=r.get("procesador"),
            color=r.get("color"),
            tipo_panel=r.get("tipo_panel"),
            resolucion=r.get("resolucion"),
        )

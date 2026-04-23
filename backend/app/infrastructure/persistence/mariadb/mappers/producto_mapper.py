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
            es_electrico=(
                bool(r["es_electrico"]) if r.get("es_electrico") is not None else None
            ),
            bateria_mah=int(r["bateria_mah"]) if r.get("bateria_mah") is not None else None,
            camara_mp=int(r["camara_mp"]) if r.get("camara_mp") is not None else None,
            camara_frontal_mp=(
                int(r["camara_frontal_mp"]) if r.get("camara_frontal_mp") is not None else None
            ),
            soporta_5g=(
                bool(r["soporta_5g"]) if r.get("soporta_5g") is not None else None
            ),
            sistema_operativo=r.get("sistema_operativo"),
            refresh_hz=int(r["refresh_hz"]) if r.get("refresh_hz") is not None else None,
            gpu=r.get("gpu"),
        )

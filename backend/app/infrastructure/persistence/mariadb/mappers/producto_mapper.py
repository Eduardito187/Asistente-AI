from __future__ import annotations

import json

from .....domain.productos import SKU, PrecioBob, Producto


class ProductoMapper:
    """Materializa un Producto desde un row crudo de MariaDB."""

    @staticmethod
    def _int(r: dict, key: str) -> int | None:
        v = r.get(key)
        return int(v) if v is not None else None

    @staticmethod
    def _float(r: dict, key: str) -> float | None:
        v = r.get(key)
        return float(v) if v is not None else None

    @staticmethod
    def _bool(r: dict, key: str) -> bool | None:
        v = r.get(key)
        return bool(v) if v is not None else None

    @classmethod
    def from_row(cls, r: dict) -> Producto:
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
                if r.get("precio_anterior_bob") is not None else None
            ),
            stock=int(r.get("stock") or 0),
            imagen_url=r.get("imagen_url"),
            activo=bool(r.get("activo")),
            pulgadas=cls._float(r, "pulgadas"),
            capacidad_gb=cls._int(r, "capacidad_gb"),
            ram_gb=cls._int(r, "ram_gb"),
            capacidad_litros=cls._float(r, "capacidad_litros"),
            capacidad_kg=cls._float(r, "capacidad_kg"),
            potencia_w=cls._int(r, "potencia_w"),
            procesador=r.get("procesador"),
            color=r.get("color"),
            tipo_panel=r.get("tipo_panel"),
            resolucion=r.get("resolucion"),
            es_electrico=cls._bool(r, "es_electrico"),
            bateria_mah=cls._int(r, "bateria_mah"),
            camara_mp=cls._int(r, "camara_mp"),
            camara_frontal_mp=cls._int(r, "camara_frontal_mp"),
            soporta_5g=cls._bool(r, "soporta_5g"),
            sistema_operativo=r.get("sistema_operativo"),
            refresh_hz=cls._int(r, "refresh_hz"),
            gpu=r.get("gpu"),
            tipo_producto=r.get("tipo_producto"),
            es_vestible=cls._bool(r, "es_vestible"),
            modelo=r.get("modelo"),
            meses_garantia=cls._int(r, "meses_garantia"),
            descripcion_extendida=r.get("descripcion_extendida"),
            caracteristicas=r.get("caracteristicas"),
            atributos=json.loads(r["atributos"]) if r.get("atributos") else None,
            es_descontinuado=bool(r.get("es_descontinuado", 0)),
        )

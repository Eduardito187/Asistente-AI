from __future__ import annotations

from typing import Iterable

from sqlalchemy import Engine, text

from ...application.ports import ProductoRepository
from ...domain.productos import ProductoRaw
from ...domain.texto import NormalizadorTexto
from .sql import ProductoSql


class MariaDbProductoRepositorio(ProductoRepository):
    """Implementación MariaDB del repo de productos (upsert por SKU)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, producto: ProductoRaw, origen: str) -> None:
        nombre_norm = NormalizadorTexto.sin_acentos((producto.nombre or "").lower())
        descripcion_norm = NormalizadorTexto.sin_acentos((producto.descripcion or "").lower()) or None
        marca_norm = NormalizadorTexto.sin_acentos((producto.marca or "").lower()) or None
        categoria_norm = NormalizadorTexto.sin_acentos((producto.categoria or "").lower()) or None

        with self._engine.begin() as conn:
            conn.execute(
                text(ProductoSql.UPSERT),
                {
                    "sku": producto.sku,
                    "nombre": producto.nombre,
                    "descripcion": producto.descripcion,
                    "categoria": producto.categoria,
                    "subcategoria": producto.subcategoria,
                    "marca": producto.marca,
                    "precio_bob": producto.precio_bob,
                    "precio_anterior_bob": producto.precio_anterior_bob,
                    "stock": producto.stock,
                    "imagen_url": producto.imagen_url,
                    "url_producto": producto.url_producto,
                    "activo": 1 if producto.activo else 0,
                    "origen": origen,
                    "nombre_norm": nombre_norm,
                    "descripcion_norm": descripcion_norm,
                    "marca_norm": marca_norm,
                    "categoria_norm": categoria_norm,
                },
            )

    def desactivar_faltantes(self, origen: str, skus_vistos: Iterable[str]) -> int:
        vistos = list(skus_vistos)
        if not vistos:
            return 0
        params: dict = {f"s{i}": s for i, s in enumerate(vistos)}
        params["o"] = origen
        with self._engine.begin() as conn:
            res = conn.execute(text(ProductoSql.desactivar_faltantes(len(vistos))), params)
            return int(res.rowcount or 0)

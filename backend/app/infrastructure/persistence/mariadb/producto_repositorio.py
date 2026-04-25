from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.productos import SKU, FiltrosAtributos, Producto, ProductoRepository
from .mappers import ProductoMapper
from .sql import ProductoSql


class MariaDbProductoRepository(ProductoRepository):

    def __init__(self, session: Session) -> None:
        self._s = session

    def obtener_por_sku(self, sku: SKU) -> Optional[Producto]:
        row = self._s.execute(
            text(ProductoSql.POR_SKU), {"s": str(sku)}
        ).mappings().first()
        return ProductoMapper.from_row(dict(row)) if row else None

    def obtener_varios(self, skus: list[SKU]) -> list[Producto]:
        if not skus:
            return []
        params = {f"s{i}": str(s) for i, s in enumerate(skus)}
        rows = self._s.execute(
            text(ProductoSql.por_skus_in(len(skus))), params
        ).mappings().all()
        return [ProductoMapper.from_row(dict(r)) for r in rows]

    def existen_skus(self, skus: list[str]) -> set[str]:
        if not skus:
            return set()
        params = {f"s{i}": s for i, s in enumerate(skus)}
        rows = self._s.execute(
            text(ProductoSql.existen_skus_in(len(skus))), params
        ).scalars().all()
        return set(rows)

    def buscar(
        self,
        query_normalizada: str,
        categoria: Optional[str],
        subcategoria: Optional[str],
        marca_normalizada: Optional[str],
        precio_min: Optional[float],
        precio_max: Optional[float],
        atributos: FiltrosAtributos,
        solo_con_stock: bool,
        limite: int,
        excluir_accesorios: bool = False,
        solo_accesorios: bool = False,
        excluir_skus: Optional[list[str]] = None,
        genero: Optional[str] = None,
        nombre_excluye: Optional[list[str]] = None,
        orden_precio: str = "asc",
    ) -> list[Producto]:
        sql, params = ProductoSql.buscar(
            query_normalizada=query_normalizada,
            categoria=categoria,
            subcategoria=subcategoria,
            marca_normalizada=marca_normalizada,
            precio_min=precio_min,
            precio_max=precio_max,
            atributos=atributos,
            solo_con_stock=solo_con_stock,
            excluir_accesorios=excluir_accesorios,
            solo_accesorios=solo_accesorios,
            excluir_skus=excluir_skus,
            genero=genero,
            nombre_excluye=nombre_excluye,
            orden_precio=orden_precio,
        )
        params["limite"] = limite
        rows = self._s.execute(text(sql), params).mappings().all()
        return [ProductoMapper.from_row(dict(r)) for r in rows]

    def skus_similares(self, sku: str, limite: int = 5) -> list[str]:
        rows = self._s.execute(
            text(ProductoSql.SKUS_SIMILARES),
            {"patron": f"%{sku[:4] or sku}%", "l": limite},
        ).scalars().all()
        return list(rows)

    def agrupar_categorias(self) -> list[dict]:
        rows = self._s.execute(text(ProductoSql.AGRUPAR_CATEGORIAS)).mappings().all()
        return [dict(r) for r in rows]

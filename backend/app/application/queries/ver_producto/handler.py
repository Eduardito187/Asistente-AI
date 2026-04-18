from __future__ import annotations

from typing import Callable

from ....domain.productos import SKU
from ...ports import UnitOfWork
from .query import VerProductoQuery
from .result import ResultadoVerProducto


class VerProductoHandler:
    """Handler CQRS: detalle + fallback a SKUs similares si no existe."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: VerProductoQuery) -> ResultadoVerProducto:
        sku = SKU(q.sku)
        with self._uow_factory() as uow:
            prod = uow.productos.obtener_por_sku(sku)
            if prod is not None:
                return ResultadoVerProducto(producto=prod, skus_similares=[])
            similares = uow.productos.skus_similares(str(sku))
            return ResultadoVerProducto(producto=None, skus_similares=similares)

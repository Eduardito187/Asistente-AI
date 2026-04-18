from __future__ import annotations

from typing import Callable

from ....domain.productos import Producto
from ....domain.shared.normalizacion import NormalizadorTexto
from ...ports import UnitOfWork
from .query import BuscarProductosQuery


class BuscarProductosHandler:
    """Handler CQRS: delega la busqueda al repo con textos normalizados."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: BuscarProductosQuery) -> list[Producto]:
        query_norm = NormalizadorTexto.normalizar(q.query)
        marca_norm = NormalizadorTexto.normalizar(q.marca) if q.marca else None
        with self._uow_factory() as uow:
            return uow.productos.buscar(
                query_normalizada=query_norm,
                categoria=q.categoria or None,
                subcategoria=q.subcategoria or None,
                marca_normalizada=marca_norm,
                precio_min=q.precio_min,
                precio_max=q.precio_max,
                solo_con_stock=q.solo_con_stock,
                limite=max(1, min(q.limite, 20)),
            )

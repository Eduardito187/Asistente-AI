from __future__ import annotations

from typing import Callable

from ....domain.productos import SKU
from ...ports import UnitOfWork
from .query import CompararProductosQuery
from .result import ResultadoCompararProductos


class CompararProductosHandler:
    """Handler CQRS: resuelve N SKUs y devuelve los que existen, respetando orden."""

    MAX_SKUS = 4

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: CompararProductosQuery) -> ResultadoCompararProductos:
        limpios = self._deduplicar(q.skus)[: self.MAX_SKUS]
        if not limpios:
            return ResultadoCompararProductos()
        with self._uow_factory() as uow:
            existentes = uow.productos.existen_skus(limpios)
            presentes = [s for s in limpios if s in existentes]
            productos = uow.productos.obtener_varios([SKU(s) for s in presentes])
            por_sku = {str(p.sku): p for p in productos}
            ordenados = [por_sku[s] for s in presentes if s in por_sku]
        faltantes = [s for s in limpios if s not in existentes]
        return ResultadoCompararProductos(productos=ordenados, skus_no_encontrados=faltantes)

    @staticmethod
    def _deduplicar(skus: tuple[str, ...]) -> list[str]:
        vistos: set[str] = set()
        orden: list[str] = []
        for s in skus or ():
            limpio = (s or "").strip().upper()
            if limpio and limpio not in vistos:
                vistos.add(limpio)
                orden.append(limpio)
        return orden

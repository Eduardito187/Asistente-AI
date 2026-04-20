from __future__ import annotations

from typing import Callable

from ....domain.productos import FiltrosAtributos, Producto
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
        atributos = FiltrosAtributos(
            pulgadas=q.pulgadas,
            pulgadas_min=q.pulgadas_min,
            pulgadas_max=q.pulgadas_max,
            capacidad_gb_min=q.capacidad_gb_min,
            ram_gb_min=q.ram_gb_min,
            capacidad_litros_min=q.capacidad_litros_min,
            capacidad_kg_min=q.capacidad_kg_min,
            potencia_w_min=q.potencia_w_min,
            potencia_w_max=q.potencia_w_max,
            procesador=q.procesador,
            tipo_panel=q.tipo_panel,
            resolucion=q.resolucion,
            color=q.color,
            es_electrico=q.es_electrico,
        )
        with self._uow_factory() as uow:
            return uow.productos.buscar(
                query_normalizada=query_norm,
                categoria=q.categoria or None,
                subcategoria=q.subcategoria or None,
                marca_normalizada=marca_norm,
                precio_min=q.precio_min,
                precio_max=q.precio_max,
                atributos=atributos,
                solo_con_stock=q.solo_con_stock,
                limite=max(1, min(q.limite, 20)),
            )

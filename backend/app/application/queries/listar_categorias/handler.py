from __future__ import annotations

from typing import Callable

from ...ports import UnitOfWork
from .query import ListarCategoriasQuery


class ListarCategoriasHandler:
    """Handler CQRS: agrupa el crudo del repo en categorias + subcategorias."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, _: ListarCategoriasQuery | None = None) -> list[dict]:
        with self._uow_factory() as uow:
            crudo = uow.productos.agrupar_categorias()
        agrupadas: dict[str, dict] = {}
        for r in crudo:
            cat = r["categoria"]
            bucket = agrupadas.setdefault(
                cat, {"categoria": cat, "cantidad": 0, "subcategorias": []}
            )
            bucket["cantidad"] += int(r["cantidad"])
            if r.get("subcategoria"):
                bucket["subcategorias"].append(
                    {"subcategoria": r["subcategoria"], "cantidad": int(r["cantidad"])}
                )
        return sorted(agrupadas.values(), key=lambda x: -x["cantidad"])

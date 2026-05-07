from __future__ import annotations

from ...domain.productos import Producto
from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery
from .filtros_duros_busqueda import FiltrosDurosBusqueda


class SugeridorProductosAlternativos:
    """SRP: dado un producto ausente (con nombre/categoria/marca estimada),
    buscar alternativas REALES que si esten en el catalogo. Ampliamos de
    especifico a generico hasta encontrar algo."""

    LIMITE = 3

    def __init__(self, buscar: BuscarProductosHandler) -> None:
        self._buscar = buscar

    def sugerir(
        self,
        categoria: str | None,
        marca: str | None,
        nombre_canonico: str | None = None,
        subcategoria: str | None = None,
        duros: FiltrosDurosBusqueda | None = None,
    ) -> list[Producto]:
        intentos = self._armar_intentos(
            categoria, subcategoria, marca, nombre_canonico,
            duros or FiltrosDurosBusqueda(),
        )
        for q in intentos:
            productos = self._buscar.ejecutar(q)
            if productos:
                return productos[: self.LIMITE]
        return []

    _COMBINACIONES: tuple[tuple[str, ...], ...] = (
        ("query", "categoria", "subcategoria", "marca"),
        ("query", "categoria", "subcategoria"),
        ("categoria", "subcategoria", "marca"),
        ("categoria", "subcategoria"),
        ("query", "categoria", "marca"),
        ("query", "categoria"),
        ("categoria", "marca"),
        ("categoria",),
    )

    def _armar_intentos(
        self,
        categoria: str | None,
        subcategoria: str | None,
        marca: str | None,
        nombre_canonico: str | None,
        duros: FiltrosDurosBusqueda,
    ) -> list[BuscarProductosQuery]:
        valores = {
            "query": (nombre_canonico or "").strip() or None,
            "categoria": (categoria or "").strip() or None,
            "subcategoria": (subcategoria or "").strip() or None,
            "marca": (marca or "").strip() or None,
        }
        duros_kwargs = duros.como_kwargs()
        exige_subcat = valores["subcategoria"] is not None
        combos = (c for c in self._COMBINACIONES if not (exige_subcat and "subcategoria" not in c))
        intentos: list[BuscarProductosQuery] = []
        vistos: set[tuple] = set()
        for combo in combos:
            query = self._intento_para(combo, valores, vistos, duros_kwargs)
            if query is not None:
                intentos.append(query)
        return intentos

    @classmethod
    def _intento_para(
        cls,
        combo: tuple[str, ...],
        valores: dict[str, str | None],
        vistos: set[tuple],
        duros: dict,
    ) -> BuscarProductosQuery | None:
        kwargs = {k: valores[k] for k in combo if valores[k]}
        if len(kwargs) != len(combo):
            return None
        clave = tuple(sorted(kwargs.items()))
        if clave in vistos:
            return None
        vistos.add(clave)
        kwargs.update(duros)
        # Accesorios (portahuevos, fundas, cables) nunca son alternativas
        # validas de un producto principal ausente en catalogo.
        kwargs["excluir_accesorios"] = True
        return BuscarProductosQuery(limite=cls.LIMITE, **kwargs)

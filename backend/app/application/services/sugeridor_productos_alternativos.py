from __future__ import annotations

from ...domain.productos import Producto
from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery


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
    ) -> list[Producto]:
        intentos = self._armar_intentos(categoria, marca, nombre_canonico)
        for q in intentos:
            productos = self._buscar.ejecutar(q)
            if productos:
                return productos[: self.LIMITE]
        return []

    _COMBINACIONES: tuple[tuple[str, ...], ...] = (
        ("query", "categoria", "marca"),
        ("query", "categoria"),
        ("query", "marca"),
        ("query",),
        ("categoria", "marca"),
        ("categoria",),
        ("marca",),
    )

    def _armar_intentos(
        self,
        categoria: str | None,
        marca: str | None,
        nombre_canonico: str | None,
    ) -> list[BuscarProductosQuery]:
        valores = {
            "query": (nombre_canonico or "").strip() or None,
            "categoria": (categoria or "").strip() or None,
            "marca": (marca or "").strip() or None,
        }
        intentos: list[BuscarProductosQuery] = []
        vistos: set[tuple] = set()
        for combo in self._COMBINACIONES:
            kwargs = {k: valores[k] for k in combo if valores[k]}
            if len(kwargs) != len(combo):
                continue
            clave = tuple(sorted(kwargs.items()))
            if clave in vistos:
                continue
            vistos.add(clave)
            intentos.append(BuscarProductosQuery(limite=self.LIMITE, **kwargs))
        return intentos

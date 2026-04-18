from __future__ import annotations

from .query import ListarCarritosQuery


class ListarCarritosHandler:
    """Handler CQRS: lee directo del read model (no toca el dominio)."""

    def __init__(self, read_model) -> None:
        self._read_model = read_model

    def ejecutar(self, q: ListarCarritosQuery) -> list[dict]:
        return self._read_model.listar(
            estado=q.estado.value if q.estado else None,
            solo_con_items=q.solo_con_items,
            limite=max(1, min(q.limite, 500)),
        )

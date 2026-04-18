from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ListarOrdenesQuery:
    """Query: listar las ultimas N ordenes confirmadas."""

    limite: int = 50

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ListarConversacionesCuradasQuery:
    """Query: pagina conversaciones curadas para el endpoint admin."""

    limite: int = 50
    offset: int = 0

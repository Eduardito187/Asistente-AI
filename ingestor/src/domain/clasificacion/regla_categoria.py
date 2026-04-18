from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReglaCategoria:
    """Regla declarativa categoria/subcategoria asociada a un patron regex."""

    categoria: str
    subcategoria: str
    patron: str

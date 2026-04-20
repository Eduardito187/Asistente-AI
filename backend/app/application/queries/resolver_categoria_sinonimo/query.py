from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResolverCategoriaSinonimoQuery:
    """Query: dado el texto libre del cliente, resolver la categoria/subcategoria
    real del catalogo que mejor lo representa. Si no hay match directo, devolver
    la categoria relacionada con mayor prioridad (fallback cruzado)."""

    texto: str
    limite_relaciones: int = 3

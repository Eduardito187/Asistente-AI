from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class SynonymCandidato:
    """Termino que aparecio repetidamente sin resolver en el catalogo.
    Cuando ocurrencias supera un umbral, se promueve a sinonimo real."""

    id: Optional[int]
    termino: str
    categoria_inferida: Optional[str]
    ocurrencias: int
    primera_vez: datetime
    ultima_vez: datetime
    promovido: bool

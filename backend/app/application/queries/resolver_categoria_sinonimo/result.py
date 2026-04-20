from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ....domain.catalogo import CategoriaRelacionada, CategoriaSinonimo


@dataclass(frozen=True)
class ResolverCategoriaSinonimoResult:
    """Resultado de ResolverCategoriaSinonimo.

    - sinonimo_directo: match exacto o por token del texto del cliente.
    - relacionadas: lista ordenada por prioridad de categorias sugeridas
      cuando el sinonimo directo apunta a algo que no tenemos en stock
      o directamente no existe en el catalogo.
    - termino_original: el texto tal como lo pidio el cliente (para razones
      conversacionales: 'no vendemos X pero si Y')."""

    termino_original: str
    sinonimo_directo: Optional[CategoriaSinonimo] = None
    relacionadas: list[CategoriaRelacionada] = field(default_factory=list)

    @property
    def tiene_match_directo(self) -> bool:
        return self.sinonimo_directo is not None

    @property
    def mejor_relacionada(self) -> Optional[CategoriaRelacionada]:
        return self.relacionadas[0] if self.relacionadas else None

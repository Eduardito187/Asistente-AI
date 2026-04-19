from __future__ import annotations

from dataclasses import dataclass, field

from .resultado_aserto import ResultadoAserto


@dataclass
class ResultadoCaso:
    """Agregado de todos los asertos de un caso dorado multi-turno."""

    nombre: str
    asertos: list[ResultadoAserto] = field(default_factory=list)

    def paso(self) -> bool:
        return all(a.ok for a in self.asertos)

    def fallidos(self) -> list[ResultadoAserto]:
        return [a for a in self.asertos if not a.ok]

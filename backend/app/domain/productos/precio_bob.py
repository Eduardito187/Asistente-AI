from __future__ import annotations

from dataclasses import dataclass

from ..shared.errors import ValorInvalido


@dataclass(frozen=True)
class PrecioBob:
    """Value Object: monto expresado en bolivianos (BOB)."""

    monto: float

    def __post_init__(self) -> None:
        if self.monto < 0:
            raise ValorInvalido("precio no puede ser negativo")
        object.__setattr__(self, "monto", round(float(self.monto), 2))

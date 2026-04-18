from __future__ import annotations

from dataclasses import dataclass

from ..shared.errors import ValorInvalido


@dataclass(frozen=True)
class SKU:
    """Value Object: identificador de un producto en el catálogo."""

    valor: str

    def __post_init__(self) -> None:
        v = (self.valor or "").strip().strip("[]").upper()
        if not v:
            raise ValorInvalido("SKU vacio")
        object.__setattr__(self, "valor", v)

    def __str__(self) -> str:
        return self.valor

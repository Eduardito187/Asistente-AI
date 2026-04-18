from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class CarritoReadModel(ABC):
    """Lectura pura contra vista_carritos (CQRS query-side)."""

    @abstractmethod
    def listar(
        self,
        estado: Optional[str],
        solo_con_items: bool,
        limite: int,
    ) -> list[dict]: ...

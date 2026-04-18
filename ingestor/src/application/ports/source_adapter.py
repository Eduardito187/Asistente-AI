from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from ...domain.productos import ProductoRaw


class SourceAdapter(ABC):
    """Puerto de entrada de datos. Cada origen concreto implementa este contrato."""

    name: str = "base"

    @abstractmethod
    def fetch(self) -> Iterable[ProductoRaw]:
        """Itera sobre productos crudos del origen. Puede ser un generator."""

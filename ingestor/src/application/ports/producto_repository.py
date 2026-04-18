from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List

from ...domain.productos import ProductoRaw


class ProductoRepository(ABC):
    """Puerto de persistencia para el catálogo de productos."""

    @abstractmethod
    def upsert(self, producto: ProductoRaw, origen: str) -> None: ...

    @abstractmethod
    def desactivar_faltantes(self, origen: str, skus_vistos: Iterable[str]) -> int:
        """Marca como inactivos los productos del origen que no aparecieron en la ingesta."""

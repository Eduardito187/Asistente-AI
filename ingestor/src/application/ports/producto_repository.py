from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List

from ...domain.productos import ProductoRaw


class ProductoRepository(ABC):
    """Puerto de persistencia para el catálogo de productos."""

    @abstractmethod
    def upsert(self, producto: ProductoRaw, origen: str) -> None: ...

    @abstractmethod
    def insertar_catalogo(self, producto: ProductoRaw, origen: str) -> bool:
        """INSERT IGNORE: inserta solo si el SKU no existe. Retorna True si fue insertado."""

    @abstractmethod
    def desactivar_faltantes(self, origen: str, skus_vistos: Iterable[str]) -> int:
        """Marca como inactivos los productos del origen que no aparecieron en la ingesta."""

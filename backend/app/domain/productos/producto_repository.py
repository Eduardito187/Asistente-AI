from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .producto import Producto
from .sku import SKU


class ProductoRepository(ABC):
    """Puerto de persistencia. La implementación vive en infrastructure/persistence."""

    @abstractmethod
    def obtener_por_sku(self, sku: SKU) -> Optional[Producto]: ...

    @abstractmethod
    def obtener_varios(self, skus: list[SKU]) -> list[Producto]: ...

    @abstractmethod
    def existen_skus(self, skus: list[str]) -> set[str]: ...

    @abstractmethod
    def buscar(
        self,
        query_normalizada: str,
        categoria: Optional[str],
        subcategoria: Optional[str],
        marca_normalizada: Optional[str],
        precio_min: Optional[float],
        precio_max: Optional[float],
        solo_con_stock: bool,
        limite: int,
    ) -> list[Producto]: ...

    @abstractmethod
    def skus_similares(self, sku: str, limite: int = 5) -> list[str]: ...

    @abstractmethod
    def agrupar_categorias(self) -> list[dict]: ...

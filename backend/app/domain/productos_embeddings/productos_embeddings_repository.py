from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .producto_embedding import ProductoEmbedding


class ProductosEmbeddingsRepository(ABC):
    """Puerto de persistencia del vector embedding por SKU."""

    @abstractmethod
    def upsert(self, embedding: ProductoEmbedding) -> None: ...

    @abstractmethod
    def obtener(self, sku: str) -> Optional[ProductoEmbedding]: ...

    @abstractmethod
    def listar_todos(self) -> list[ProductoEmbedding]: ...

    @abstractmethod
    def skus_sin_embedding(self, modelo: str) -> list[str]: ...

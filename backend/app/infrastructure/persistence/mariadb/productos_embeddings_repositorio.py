from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.productos_embeddings import (
    ProductoEmbedding,
    ProductosEmbeddingsRepository,
)
from .mappers import ProductoEmbeddingMapper
from .sql import ProductoEmbeddingSql


class MariaDbProductosEmbeddingsRepository(ProductosEmbeddingsRepository):
    """Impl MariaDB del repo de ProductoEmbedding."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def upsert(self, embedding: ProductoEmbedding) -> None:
        self._s.execute(
            text(ProductoEmbeddingSql.UPSERT),
            {
                "sku": embedding.sku,
                "modelo": embedding.modelo,
                "vector": embedding.vector,
            },
        )

    def obtener(self, sku: str) -> Optional[ProductoEmbedding]:
        row = (
            self._s.execute(text(ProductoEmbeddingSql.POR_SKU), {"sku": sku})
            .mappings()
            .first()
        )
        return ProductoEmbeddingMapper.from_row(dict(row)) if row else None

    def listar_todos(self) -> list[ProductoEmbedding]:
        rows = self._s.execute(text(ProductoEmbeddingSql.LISTAR_TODOS)).mappings().all()
        return [ProductoEmbeddingMapper.from_row(dict(r)) for r in rows]

    def skus_sin_embedding(self, modelo: str) -> list[str]:
        rows = (
            self._s.execute(text(ProductoEmbeddingSql.SKUS_SIN_EMBEDDING), {"modelo": modelo})
            .scalars()
            .all()
        )
        return list(rows)

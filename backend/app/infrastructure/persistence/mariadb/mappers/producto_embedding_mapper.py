from __future__ import annotations

from .....domain.productos_embeddings import ProductoEmbedding


class ProductoEmbeddingMapper:
    """Materializa un ProductoEmbedding desde un row crudo de MariaDB."""

    @staticmethod
    def from_row(r: dict) -> ProductoEmbedding:
        return ProductoEmbedding(
            sku=r["sku"],
            modelo=r["modelo"],
            vector=bytes(r["vector"]),
            updated_at=r["updated_at"],
        )

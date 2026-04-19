from __future__ import annotations


class ProductoEmbeddingSql:
    """Catalogo SQL de los vectores de embedding de productos.

    Nota: `vector` es palabra reservada desde MariaDB 11.7, por eso va con backticks.
    """

    UPSERT = (
        "INSERT INTO productos_embeddings (sku, modelo, `vector`) "
        "VALUES (:sku, :modelo, :vector) "
        "ON DUPLICATE KEY UPDATE modelo = VALUES(modelo), `vector` = VALUES(`vector`)"
    )

    POR_SKU = (
        "SELECT sku, modelo, `vector`, updated_at "
        "FROM productos_embeddings WHERE sku = :sku"
    )

    LISTAR_TODOS = (
        "SELECT sku, modelo, `vector`, updated_at FROM productos_embeddings"
    )

    SKUS_SIN_EMBEDDING = (
        "SELECT p.sku FROM productos p "
        "LEFT JOIN productos_embeddings e ON e.sku = p.sku AND e.modelo = :modelo "
        "WHERE p.activo = 1 AND e.sku IS NULL"
    )

from __future__ import annotations


class CarritoSql:
    """Catalogo SQL del agregado Carrito."""

    OBTENER_ITEMS = (
        "SELECT c.sku, c.cantidad, p.nombre, p.precio_bob "
        "FROM carrito_items c JOIN productos p ON p.sku = c.sku "
        "WHERE c.sesion_id = :s ORDER BY c.created_at"
    )

    AGREGAR_O_INCREMENTAR = (
        "INSERT INTO carrito_items (sesion_id, sku, cantidad) "
        "VALUES (:s, :sku, :c) "
        "ON DUPLICATE KEY UPDATE cantidad = cantidad + VALUES(cantidad)"
    )

    QUITAR_ITEM = "DELETE FROM carrito_items WHERE sesion_id = :s AND sku = :sku"

    VACIAR = "DELETE FROM carrito_items WHERE sesion_id = :s"

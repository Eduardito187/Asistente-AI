from __future__ import annotations


class OrdenSql:
    """Catalogo SQL del agregado Orden."""

    INSERTAR_ORDEN = (
        "INSERT INTO ordenes "
        "(id, sesion_id, cliente_nombre, cliente_email, cliente_telefono, "
        " total_bob, items_cantidad, estado, notas) "
        "VALUES (:id, :sid, :n, :e, :t, :tot, :c, :estado, :notas)"
    )

    INSERTAR_ITEM = (
        "INSERT INTO orden_items "
        "(orden_id, sku, nombre, marca, cantidad, precio_unitario_bob, subtotal_bob) "
        "VALUES (:o, :sku, :nom, :m, :c, :pu, :sub)"
    )

    RELEER_NUMERO_Y_FECHA = "SELECT numero_orden, created_at FROM ordenes WHERE id = :id"

    POR_NUMERO = "SELECT * FROM ordenes WHERE numero_orden = :n"

    POR_SESION = "SELECT * FROM ordenes WHERE sesion_id = :s ORDER BY created_at DESC"

    LISTAR = "SELECT * FROM ordenes ORDER BY created_at DESC LIMIT :l"

    CARGAR_ITEMS = (
        "SELECT sku, nombre, marca, cantidad, precio_unitario_bob, subtotal_bob "
        "FROM orden_items WHERE orden_id = :o"
    )

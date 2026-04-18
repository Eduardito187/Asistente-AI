from __future__ import annotations


class SesionSql:
    """Catalogo SQL del agregado Sesion."""

    CREAR = (
        "INSERT INTO sesiones (id, carrito_estado, ultima_actividad_at) "
        "VALUES (:id, :estado, NOW(6))"
    )

    POR_ID = "SELECT * FROM sesiones WHERE id = :id"

    EXISTE = "SELECT 1 FROM sesiones WHERE id = :id"

    ACTUALIZAR = (
        "UPDATE sesiones SET carrito_estado = :estado, "
        "cliente_nombre = :n, cliente_email = :e, cliente_telefono = :t, "
        "ultima_actividad_at = :ult WHERE id = :id"
    )

    TOCAR = "UPDATE sesiones SET ultima_actividad_at = NOW(6) WHERE id = :id"

    MARCAR_ABANDONADAS = (
        "UPDATE sesiones s "
        "JOIN (SELECT DISTINCT sesion_id FROM carrito_items) ci ON ci.sesion_id = s.id "
        "SET s.carrito_estado = 'abandonado' "
        "WHERE s.carrito_estado = 'activo' "
        "AND s.ultima_actividad_at < (NOW() - INTERVAL :h HOUR)"
    )

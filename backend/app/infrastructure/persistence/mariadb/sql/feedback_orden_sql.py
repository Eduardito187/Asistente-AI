from __future__ import annotations


class FeedbackOrdenSql:
    """Catalogo SQL del agregado FeedbackOrden."""

    REGISTRAR = (
        "INSERT INTO feedback_ordenes (orden_id, sesion_id, rating, comentario) "
        "VALUES (:oid, :sid, :rating, :comentario) "
        "ON DUPLICATE KEY UPDATE rating = VALUES(rating), comentario = VALUES(comentario)"
    )

    POR_ORDEN = (
        "SELECT id, orden_id, sesion_id, rating, comentario, created_at "
        "FROM feedback_ordenes WHERE orden_id = :oid"
    )

    ULTIMA_ORDEN_SIN_FEEDBACK = (
        "SELECT o.id FROM ordenes o "
        "LEFT JOIN feedback_ordenes f ON f.orden_id = o.id "
        "WHERE o.sesion_id = :sid AND f.id IS NULL "
        "ORDER BY o.created_at DESC LIMIT 1"
    )

    LISTAR_RECIENTES = (
        "SELECT id, orden_id, sesion_id, rating, comentario, created_at "
        "FROM feedback_ordenes ORDER BY created_at DESC LIMIT :lim"
    )

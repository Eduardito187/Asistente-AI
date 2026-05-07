from __future__ import annotations


class FeedbackTurnosSql:
    """Catalogo SQL del agregado FeedbackTurno."""

    INSERT = (
        "INSERT INTO feedback_turnos "
        "(sesion_id, turno_index, mensaje_usuario, respuesta_agente, voto, comentario) "
        "VALUES (:sid, :idx, :msg, :resp, :voto, :comm)"
    )

    LISTAR_POR_VOTO = (
        "SELECT id, sesion_id, turno_index, mensaje_usuario, respuesta_agente, "
        "voto, comentario, creado_en "
        "FROM feedback_turnos WHERE voto = :voto "
        "ORDER BY creado_en DESC LIMIT :limite"
    )

    STATS = (
        "SELECT voto, COUNT(*) AS total "
        "FROM feedback_turnos GROUP BY voto"
    )

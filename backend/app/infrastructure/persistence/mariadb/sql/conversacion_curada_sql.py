from __future__ import annotations


class ConversacionCuradaSql:
    """Catalogo SQL del agregado ConversacionCurada."""

    INSERTAR = (
        "INSERT INTO conversaciones_curadas "
        "(sesion_id, etiqueta, cliente_texto, asistente_texto, score, turnos, "
        "llevo_a_orden, activa) "
        "VALUES (:sesion_id, :etiqueta, :cliente, :asistente, :score, :turnos, "
        ":llevo, :activa)"
    )

    ACTUALIZAR = (
        "UPDATE conversaciones_curadas SET "
        "etiqueta = :etiqueta, cliente_texto = :cliente, asistente_texto = :asistente, "
        "score = :score, turnos = :turnos, llevo_a_orden = :llevo, activa = :activa "
        "WHERE id = :id"
    )

    POR_SESION = (
        "SELECT id, sesion_id, etiqueta, cliente_texto, asistente_texto, score, "
        "turnos, llevo_a_orden, activa, created_at, updated_at "
        "FROM conversaciones_curadas WHERE sesion_id = :sesion_id"
    )

    TOP_ACTIVAS = (
        "SELECT id, sesion_id, etiqueta, cliente_texto, asistente_texto, score, "
        "turnos, llevo_a_orden, activa, created_at, updated_at "
        "FROM conversaciones_curadas "
        "WHERE activa = 1 "
        "ORDER BY score DESC, updated_at DESC "
        "LIMIT :limite"
    )

    LISTAR = (
        "SELECT id, sesion_id, etiqueta, cliente_texto, asistente_texto, score, "
        "turnos, llevo_a_orden, activa, created_at, updated_at "
        "FROM conversaciones_curadas "
        "ORDER BY score DESC, updated_at DESC "
        "LIMIT :limite OFFSET :offset"
    )

    SET_ACTIVA = "UPDATE conversaciones_curadas SET activa = :activa WHERE id = :id"

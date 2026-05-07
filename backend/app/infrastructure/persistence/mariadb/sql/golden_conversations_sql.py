from __future__ import annotations


class GoldenConversationsSql:
    UPSERT = (
        "INSERT INTO golden_conversations "
        "(caso_que_cubre, categoria, intencion, uso, cliente_texto, asistente_texto, "
        " prioridad, activo, errores_que_previene) "
        "VALUES (:caso, :cat, :intencion, :uso, :cliente, :asistente, :prio, :activo, :errores) "
        "ON DUPLICATE KEY UPDATE "
        "categoria = VALUES(categoria), intencion = VALUES(intencion), "
        "uso = VALUES(uso), cliente_texto = VALUES(cliente_texto), "
        "asistente_texto = VALUES(asistente_texto), prioridad = VALUES(prioridad), "
        "activo = VALUES(activo), errores_que_previene = VALUES(errores_que_previene)"
    )

    LISTAR_ACTIVAS = (
        "SELECT id, caso_que_cubre, categoria, intencion, uso, cliente_texto, "
        "asistente_texto, prioridad, activo, errores_que_previene, created_at, updated_at "
        "FROM golden_conversations WHERE activo = 1 "
        "ORDER BY prioridad DESC, id DESC LIMIT :limite"
    )

    POR_CATEGORIA = (
        "SELECT id, caso_que_cubre, categoria, intencion, uso, cliente_texto, "
        "asistente_texto, prioridad, activo, errores_que_previene, created_at, updated_at "
        "FROM golden_conversations "
        "WHERE activo = 1 AND categoria = :cat "
        "AND (:intencion IS NULL OR intencion = :intencion OR intencion IS NULL) "
        "ORDER BY prioridad DESC LIMIT :limite"
    )

    DESACTIVAR = (
        "UPDATE golden_conversations SET activo = 0 WHERE caso_que_cubre = :caso"
    )

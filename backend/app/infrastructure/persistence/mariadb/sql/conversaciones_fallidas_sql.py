from __future__ import annotations


class ConversacionesFallidasSql:
    """Catalogo SQL del agregado ConversacionFallida."""

    INSERT = (
        "INSERT INTO conversaciones_fallidas "
        "(sesion_id, mensaje_usuario, perfil_estado, ultimo_buscar_args, "
        " razon_fallo, trace_resumen) "
        "VALUES (:sid, :msg, :perfil, :args, :razon, :trace)"
    )

    LISTAR_RECIENTES = (
        "SELECT id, sesion_id, mensaje_usuario, perfil_estado, ultimo_buscar_args, "
        "razon_fallo, trace_resumen, creado_en "
        "FROM conversaciones_fallidas "
        "ORDER BY creado_en DESC LIMIT :limite"
    )

    CONTAR_POR_RAZON = (
        "SELECT razon_fallo, COUNT(*) AS total "
        "FROM conversaciones_fallidas GROUP BY razon_fallo"
    )

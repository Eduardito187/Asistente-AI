from __future__ import annotations


class IngestaLogSql:
    """Catalogo SQL del log de ingestas."""

    INICIAR = "INSERT INTO ingestas_log (origen, estado) VALUES (:o, 'en_curso')"

    COMPLETAR = (
        "UPDATE ingestas_log "
        "SET fin = NOW(6), productos_procesados = :n, estado = 'ok' "
        "WHERE id = :id"
    )

    FALLAR = (
        "UPDATE ingestas_log "
        "SET fin = NOW(6), estado = 'error', error = :e "
        "WHERE id = :id"
    )

    HEALTH = "SELECT 1"

from __future__ import annotations


class DashboardMetricasSql:
    """Catalogo SQL para reportes agregados sobre metricas_turno."""

    RESUMEN_GLOBAL = (
        "SELECT "
        "  COUNT(*)                                          AS turnos, "
        "  AVG(tiempo_ms)                                    AS avg_ms, "
        "  SUM(CASE WHEN mentiras_detectadas > 0 THEN 1 ELSE 0 END) AS turnos_con_mentiras, "
        "  SUM(tool_calls)                                   AS tool_calls, "
        "  COUNT(DISTINCT sesion_id)                         AS sesiones "
        "FROM metricas_turno "
        "WHERE created_at >= (NOW() - INTERVAL :dias DAY)"
    )

    POR_RUTA = (
        "SELECT ruta, COUNT(*) AS turnos, AVG(tiempo_ms) AS avg_ms "
        "FROM metricas_turno "
        "WHERE created_at >= (NOW() - INTERVAL :dias DAY) "
        "GROUP BY ruta ORDER BY turnos DESC"
    )

    LATENCIAS = (
        "SELECT tiempo_ms FROM metricas_turno "
        "WHERE created_at >= (NOW() - INTERVAL :dias DAY) "
        "ORDER BY tiempo_ms"
    )

    SESIONES_QUE_CERRARON = (
        "SELECT COUNT(DISTINCT o.sesion_id) "
        "FROM ordenes o "
        "WHERE o.created_at >= (NOW() - INTERVAL :dias DAY)"
    )

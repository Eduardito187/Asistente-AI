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

    # Top categorías buscadas (JOIN con perfiles para saber categoría del turno)
    TOP_CATEGORIAS = (
        "SELECT p.categoria_foco AS categoria, COUNT(*) AS turnos "
        "FROM metricas_turno m "
        "JOIN perfiles_sesion p ON p.sesion_id = m.sesion_id "
        "WHERE m.created_at >= (NOW() - INTERVAL :dias DAY) "
        "  AND p.categoria_foco IS NOT NULL "
        "GROUP BY p.categoria_foco "
        "ORDER BY turnos DESC LIMIT 10"
    )

    # Top ciudades (JOIN con perfiles)
    TOP_CIUDADES = (
        "SELECT p.ciudad_sesion AS ciudad, COUNT(DISTINCT m.sesion_id) AS sesiones "
        "FROM metricas_turno m "
        "JOIN perfiles_sesion p ON p.sesion_id = m.sesion_id "
        "WHERE m.created_at >= (NOW() - INTERVAL :dias DAY) "
        "  AND p.ciudad_sesion IS NOT NULL "
        "GROUP BY p.ciudad_sesion "
        "ORDER BY sesiones DESC LIMIT 10"
    )

    # Tasa de búsquedas sin resultado (ruta = 'producto_ausente' o 'sin_resultado')
    TASA_SIN_RESULTADO = (
        "SELECT "
        "  COUNT(*) AS total_busquedas, "
        "  SUM(CASE WHEN ruta IN ('producto_ausente','manejador_producto_ausente') THEN 1 ELSE 0 END) AS sin_resultado, "
        "  ROUND(100.0 * SUM(CASE WHEN ruta IN ('producto_ausente','manejador_producto_ausente') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS pct_sin_resultado "
        "FROM metricas_turno "
        "WHERE created_at >= (NOW() - INTERVAL :dias DAY)"
    )

    # Tasa de derivación a humano
    TASA_DERIVACION = (
        "SELECT "
        "  COUNT(*) AS total_turnos, "
        "  SUM(CASE WHEN ruta IN ('derivar_ventas','frustracion_alta') THEN 1 ELSE 0 END) AS derivados, "
        "  ROUND(100.0 * SUM(CASE WHEN ruta IN ('derivar_ventas','frustracion_alta') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS pct_derivacion "
        "FROM metricas_turno "
        "WHERE created_at >= (NOW() - INTERVAL :dias DAY)"
    )

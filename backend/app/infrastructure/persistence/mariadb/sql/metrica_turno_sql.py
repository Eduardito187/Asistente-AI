from __future__ import annotations


class MetricaTurnoSql:
    """Catalogo SQL del agregado MetricaTurno."""

    REGISTRAR = (
        "INSERT INTO metricas_turno "
        "(sesion_id, mensaje_usuario_len, respuesta_len, tool_calls, "
        "mentiras_detectadas, productos_citados, ruta, tiempo_ms) "
        "VALUES (:sesion_id, :mlen, :rlen, :tools, :mentiras, :prods, :ruta, :ms)"
    )

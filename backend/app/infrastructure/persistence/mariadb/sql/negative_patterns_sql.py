from __future__ import annotations


class NegativePatternsSql:
    UPSERT = (
        "INSERT INTO negative_patterns (patron, reason_code, descripcion, activo) "
        "VALUES (:patron, :reason, :desc, :activo) "
        "ON DUPLICATE KEY UPDATE "
        "reason_code = VALUES(reason_code), descripcion = VALUES(descripcion), "
        "activo = VALUES(activo)"
    )

    LISTAR_ACTIVOS = (
        "SELECT id, patron, reason_code, descripcion, activo, ocurrencias_observadas, created_at "
        "FROM negative_patterns WHERE activo = 1 ORDER BY ocurrencias_observadas DESC"
    )

    INCREMENTAR = (
        "UPDATE negative_patterns SET ocurrencias_observadas = ocurrencias_observadas + 1 "
        "WHERE patron = :patron"
    )

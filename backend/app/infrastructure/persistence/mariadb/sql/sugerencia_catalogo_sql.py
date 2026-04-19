from __future__ import annotations


class SugerenciaCatalogoSql:
    """Catalogo SQL del agregado SugerenciaCatalogo."""

    POR_NOMBRE_NORM = (
        "SELECT id, nombre, nombre_norm, categoria_estimada, marca_estimada, "
        "veces_solicitado, primer_contexto_cliente, primera_fecha, ultima_fecha "
        "FROM sugerencias_catalogo WHERE nombre_norm = :nombre_norm"
    )

    INSERTAR = (
        "INSERT INTO sugerencias_catalogo "
        "(nombre, nombre_norm, categoria_estimada, marca_estimada, "
        "veces_solicitado, primer_contexto_cliente, primera_fecha, ultima_fecha) "
        "VALUES (:nombre, :nombre_norm, :categoria, :marca, 1, :contexto, NOW(6), NOW(6))"
    )

    INCREMENTAR = (
        "UPDATE sugerencias_catalogo "
        "SET veces_solicitado = veces_solicitado + 1, ultima_fecha = NOW(6) "
        "WHERE nombre_norm = :nombre_norm"
    )

from __future__ import annotations


class SynonymsCandidatosSql:
    """Catalogo SQL del agregado SynonymCandidato."""

    UPSERT = (
        "INSERT INTO synonyms_candidatos (termino, categoria_inferida) "
        "VALUES (:termino, :cat) "
        "ON DUPLICATE KEY UPDATE "
        "ocurrencias = ocurrencias + 1, "
        "categoria_inferida = COALESCE(VALUES(categoria_inferida), categoria_inferida), "
        "ultima_vez = CURRENT_TIMESTAMP"
    )

    OBTENER_OCURRENCIAS = (
        "SELECT ocurrencias FROM synonyms_candidatos WHERE termino = :termino"
    )

    LISTAR_TOP = (
        "SELECT id, termino, categoria_inferida, ocurrencias, primera_vez, "
        "ultima_vez, promovido "
        "FROM synonyms_candidatos "
        "WHERE (:solo_no_promovidos = 0 OR promovido = 0) "
        "ORDER BY ocurrencias DESC, ultima_vez DESC "
        "LIMIT :limite"
    )

    MARCAR_PROMOVIDO = (
        "UPDATE synonyms_candidatos SET promovido = 1 WHERE id = :id_"
    )

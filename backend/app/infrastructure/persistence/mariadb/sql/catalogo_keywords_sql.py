from __future__ import annotations


class CatalogoKeywordsSql:
    """Catalogo SQL del agregado Catalogo (sinonimos, relaciones, keywords).
    Todas las consultas viven aqui."""

    SINONIMO_POR_PALABRA_NORM = (
        "SELECT palabra_clave, palabra_clave_norm, categoria, subcategoria, "
        "sku_especifico, CAST(confianza AS DECIMAL(3,2)) AS confianza "
        "FROM categorias_sinonimos WHERE palabra_clave_norm = :palabra "
        "ORDER BY confianza DESC LIMIT 1"
    )

    RELACIONES_POR_ORIGEN = (
        "SELECT categoria_origen, categoria_sugerida, subcategoria_sugerida, "
        "razon, prioridad FROM categorias_relacionadas "
        "WHERE LOWER(categoria_origen) = :origen "
        "ORDER BY prioridad ASC LIMIT :limite"
    )

    SKUS_POR_KEYWORD = (
        "SELECT pk.sku FROM producto_keywords pk "
        "INNER JOIN productos p ON p.sku = pk.sku AND p.activo = 1 AND p.stock > 0 "
        "WHERE pk.keyword_norm = :kw ORDER BY p.precio_bob DESC LIMIT :limite"
    )

    SINONIMOS_PREFIJO_FUZZY = (
        "SELECT palabra_clave, palabra_clave_norm, categoria, subcategoria, "
        "sku_especifico, CAST(confianza AS DECIMAL(3,2)) AS confianza "
        "FROM categorias_sinonimos "
        "WHERE SUBSTRING(palabra_clave_norm, 1, :prefix_len) = :prefijo "
        "AND ABS(CHAR_LENGTH(palabra_clave_norm) - :token_len) <= 2 "
        "ORDER BY confianza DESC LIMIT :limite"
    )

    @staticmethod
    def sinonimos_por_tokens_in(n: int) -> str:
        placeholders = ", ".join(f":t{i}" for i in range(n))
        return (
            "SELECT palabra_clave, palabra_clave_norm, categoria, subcategoria, "
            "sku_especifico, CAST(confianza AS DECIMAL(3,2)) AS confianza "
            "FROM categorias_sinonimos "
            f"WHERE palabra_clave_norm IN ({placeholders}) "
            "ORDER BY confianza DESC LIMIT :limite"
        )

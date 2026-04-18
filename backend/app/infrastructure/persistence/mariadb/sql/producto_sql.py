from __future__ import annotations

from typing import Optional

from ....domain.shared.tokens_consulta import TokensConsulta


class ProductoSql:
    """Catalogo SQL del agregado Producto. Todas las consultas viven aqui."""

    POR_SKU = "SELECT * FROM productos WHERE sku = :s"

    SKUS_SIMILARES = (
        "SELECT sku FROM productos "
        "WHERE activo = 1 AND sku LIKE :patron "
        "ORDER BY CHAR_LENGTH(sku) ASC LIMIT :l"
    )

    AGRUPAR_CATEGORIAS = (
        "SELECT categoria, subcategoria, COUNT(*) AS cantidad "
        "FROM productos WHERE activo = 1 AND stock > 0 AND categoria IS NOT NULL "
        "GROUP BY categoria, subcategoria ORDER BY categoria, cantidad DESC"
    )

    _MATCH_EXPR = (
        "MATCH(nombre_norm, descripcion_norm, marca_norm, categoria_norm) "
        "AGAINST (:q IN BOOLEAN MODE)"
    )

    @staticmethod
    def tokens_boolean(query_normalizada: str) -> str:
        """Convierte 'laptop disponibles' en '+laptop*' filtrando stopwords y tokens cortos."""
        return " ".join(f"+{t}*" for t in TokensConsulta.significativos(query_normalizada))

    @staticmethod
    def por_skus_in(n: int) -> str:
        placeholders = ", ".join(f":s{i}" for i in range(n))
        return f"SELECT * FROM productos WHERE sku IN ({placeholders})"

    @staticmethod
    def existen_skus_in(n: int) -> str:
        placeholders = ", ".join(f":s{i}" for i in range(n))
        return f"SELECT sku FROM productos WHERE sku IN ({placeholders})"

    @classmethod
    def buscar(
        cls,
        query_normalizada: str,
        categoria: Optional[str],
        subcategoria: Optional[str],
        marca_normalizada: Optional[str],
        precio_min: Optional[float],
        precio_max: Optional[float],
        solo_con_stock: bool,
    ) -> tuple[str, dict]:
        """Construye SELECT dinamico para buscar productos. Devuelve (sql, params)."""
        clauses = ["activo = 1"]
        params: dict = {}
        order_parts: list[str] = []

        if solo_con_stock:
            clauses.append("stock > 0")
        q_boolean = cls.tokens_boolean(query_normalizada) if query_normalizada else ""
        if q_boolean:
            clauses.append(cls._MATCH_EXPR)
            params["q"] = q_boolean
            order_parts.append(f"{cls._MATCH_EXPR} DESC")
        if categoria:
            clauses.append("LOWER(categoria) LIKE :cat")
            params["cat"] = f"%{categoria.lower()}%"
        if subcategoria:
            clauses.append("LOWER(subcategoria) LIKE :sub")
            params["sub"] = f"%{subcategoria.lower()}%"
        if marca_normalizada:
            clauses.append("marca_norm LIKE :marca")
            params["marca"] = f"%{marca_normalizada}%"
        if precio_min is not None:
            clauses.append("precio_bob >= :pmin")
            params["pmin"] = precio_min
        if precio_max is not None:
            clauses.append("precio_bob <= :pmax")
            params["pmax"] = precio_max

        order_parts.append("precio_bob ASC")
        sql = (
            f"SELECT * FROM productos WHERE {' AND '.join(clauses)} "
            f"ORDER BY {', '.join(order_parts)} LIMIT :limite"
        )
        return sql, params

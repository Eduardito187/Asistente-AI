from __future__ import annotations

from typing import Optional

from .....domain.productos import FiltrosAtributos
from .....domain.shared.tokens_consulta import TokensConsulta


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
        "MATCH(nombre_norm, marca_norm, categoria_norm) "
        "AGAINST (:q IN BOOLEAN MODE)"
    )

    LONGITUD_MINIMA_PREFIJO = 5

    @classmethod
    def _raiz_para_like(cls, token: str) -> str:
        """Reduce plurales simples para LIKE: 'televisores' -> 'televisor'.
        Evita que el boost por nombre se pierda por singular/plural."""
        for sufijo in ("es", "s"):
            if len(token) > cls.LONGITUD_MINIMA_PREFIJO and token.endswith(sufijo):
                return token[: -len(sufijo)]
        return token

    @classmethod
    def tokens_boolean(cls, query_normalizada: str) -> str:
        """Convierte 'laptop acer' en '+laptop* +acer' filtrando stopwords.

        Tokens cortos (<5 chars) se buscan exactos para evitar falsos positivos
        por prefijo (ej. 'acer' no debe matchear 'acero'). Tokens largos
        mantienen el wildcard para aceptar plurales/variantes.
        """
        partes = []
        for t in TokensConsulta.significativos(query_normalizada):
            sufijo = "*" if len(t) >= cls.LONGITUD_MINIMA_PREFIJO else ""
            partes.append(f"+{t}{sufijo}")
        return " ".join(partes)

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
        atributos: FiltrosAtributos,
        solo_con_stock: bool,
        excluir_accesorios: bool = False,
        solo_accesorios: bool = False,
        excluir_skus: Optional[list[str]] = None,
        genero: Optional[str] = None,
    ) -> tuple[str, dict]:
        """Construye SELECT dinamico para buscar productos. Devuelve (sql, params)."""
        clauses = ["activo = 1"]
        params: dict = {}
        order_parts: list[str] = []

        if solo_con_stock:
            clauses.append("stock > 0")
        cls._agregar_filtro_accesorios(clauses, excluir_accesorios, solo_accesorios)
        cls._agregar_exclusion_skus(clauses, params, excluir_skus)
        cls._agregar_filtro_genero(clauses, params, genero)
        q_boolean = cls.tokens_boolean(query_normalizada) if query_normalizada else ""
        if q_boolean:
            clauses.append(cls._MATCH_EXPR)
            params["q"] = q_boolean
            tokens_largos = [
                t for t in TokensConsulta.significativos(query_normalizada)
                if len(t) >= cls.LONGITUD_MINIMA_PREFIJO
            ]
            if tokens_largos:
                likes = []
                for i, t in enumerate(tokens_largos):
                    key = f"tokn{i}"
                    likes.append(f"nombre_norm LIKE :{key}")
                    params[key] = f"%{cls._raiz_para_like(t)}%"
                order_parts.append(
                    f"(CASE WHEN {' OR '.join(likes)} THEN 1 ELSE 0 END) DESC"
                )
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
        cls._agregar_filtros_atributos(clauses, params, atributos)

        order_parts.append("precio_bob ASC")
        sql = (
            f"SELECT * FROM productos WHERE {' AND '.join(clauses)} "
            f"ORDER BY {', '.join(order_parts)} LIMIT :limite"
        )
        return sql, params

    @staticmethod
    def _agregar_filtro_accesorios(
        clauses: list, excluir_accesorios: bool, solo_accesorios: bool
    ) -> None:
        if solo_accesorios:
            clauses.append("es_accesorio = 1")
        elif excluir_accesorios:
            clauses.append("es_accesorio = 0")

    @staticmethod
    def _agregar_filtro_genero(
        clauses: list, params: dict, genero: Optional[str]
    ) -> None:
        """Filtra ESTRICTO por ENUM productos.genero (acepta unisex junto al
        pedido, pero NO neutros NULL). Si el caller necesita fallback a
        neutros cuando no hay match, debe re-ejecutar sin este filtro."""
        if not genero:
            return
        clauses.append("(genero = :genero OR genero = 'unisex')")
        params["genero"] = genero

    @staticmethod
    def _agregar_exclusion_skus(
        clauses: list, params: dict, excluir_skus: Optional[list[str]]
    ) -> None:
        if not excluir_skus:
            return
        placeholders = []
        for i, sku in enumerate(excluir_skus):
            key = f"exs{i}"
            placeholders.append(f":{key}")
            params[key] = sku
        if placeholders:
            clauses.append(f"sku NOT IN ({', '.join(placeholders)})")

    @staticmethod
    def _agregar_filtros_atributos(
        clauses: list, params: dict, a: FiltrosAtributos
    ) -> None:
        """Anade WHERE sobre columnas estructuradas (pulgadas, GB, etc.).

        Tolerancia de +/-0.5 en pulgadas exactas: '55 pulgadas' debe aceptar 55.0 o 55.5.
        """
        if a.pulgadas is not None:
            clauses.append("pulgadas BETWEEN :pul_lo AND :pul_hi")
            params["pul_lo"] = a.pulgadas - 0.5
            params["pul_hi"] = a.pulgadas + 0.5
        if a.pulgadas_min is not None:
            clauses.append("pulgadas >= :pul_min")
            params["pul_min"] = a.pulgadas_min
        if a.pulgadas_max is not None:
            clauses.append("pulgadas <= :pul_max")
            params["pul_max"] = a.pulgadas_max
        if a.capacidad_gb_min is not None:
            clauses.append("capacidad_gb >= :cap_gb_min")
            params["cap_gb_min"] = a.capacidad_gb_min
        if a.ram_gb_min is not None:
            clauses.append("ram_gb >= :ram_min")
            params["ram_min"] = a.ram_gb_min
        if a.capacidad_litros_min is not None:
            clauses.append("capacidad_litros >= :lt_min")
            params["lt_min"] = a.capacidad_litros_min
        if a.capacidad_kg_min is not None:
            clauses.append("capacidad_kg >= :kg_min")
            params["kg_min"] = a.capacidad_kg_min
        if a.potencia_w_min is not None:
            clauses.append("potencia_w >= :pw_min")
            params["pw_min"] = a.potencia_w_min
        if a.potencia_w_max is not None:
            clauses.append("potencia_w <= :pw_max")
            params["pw_max"] = a.potencia_w_max
        if a.procesador:
            clauses.append("LOWER(procesador) = :proc")
            params["proc"] = a.procesador.lower()
        if a.tipo_panel:
            clauses.append("UPPER(tipo_panel) = :panel")
            params["panel"] = a.tipo_panel.upper()
        if a.resolucion:
            clauses.append("UPPER(resolucion) = :resol")
            params["resol"] = a.resolucion.upper()
        if a.color:
            clauses.append("LOWER(color) = :col")
            params["col"] = a.color.lower()
        if a.es_electrico is not None:
            clauses.append("es_electrico = :elec")
            params["elec"] = 1 if a.es_electrico else 0

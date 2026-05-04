from __future__ import annotations

from typing import Optional

from .....domain.productos import FiltrosAtributos, OpcionesBusqueda
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
        """Convierte 'laptop acer' en '+laptop* acer*' filtrando stopwords.

        Solo el PRIMER token es requerido (+). Los tokens adicionales son
        boosts opcionales: suben el score pero no matan la búsqueda cuando
        el cliente incluye palabras de contexto no-producto ('bacin para ninho'
        → '+bacin* ninho*' — encuentra bacinillas aunque 'ninho' no exista
        en ningun nombre).

        Tokens cortos (<5 chars) se buscan exactos para evitar falsos positivos
        por prefijo (ej. 'acer' no debe matchear 'acero'). Tokens largos
        mantienen el wildcard para aceptar plurales/variantes.
        """
        partes = []
        for i, t in enumerate(TokensConsulta.significativos(query_normalizada)):
            sufijo = "*" if len(t) >= cls.LONGITUD_MINIMA_PREFIJO else ""
            prefijo = "+" if i == 0 else ""
            partes.append(f"{prefijo}{t}{sufijo}")
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
        opciones: OpcionesBusqueda,
    ) -> tuple[str, dict]:
        """Construye SELECT dinamico para buscar productos. Devuelve (sql, params)."""
        clauses = ["(activo = 1 OR es_descontinuado = 1)"]
        params: dict = {}
        order_parts: list[str] = []

        cls._agregar_flags_basicos(clauses, opciones.solo_con_stock, opciones.solo_en_oferta)
        cls._agregar_filtro_accesorios(clauses, opciones.excluir_accesorios, opciones.solo_accesorios)
        cls._agregar_exclusion_skus(clauses, params, opciones.excluir_skus)
        cls._agregar_filtro_genero(clauses, params, opciones.genero)
        cls._agregar_exclusion_nombre(clauses, params, opciones.nombre_excluye)
        cls._agregar_clausula_fulltext(clauses, params, order_parts, query_normalizada)
        cls._agregar_filtros_jerarquia(
            clauses, params, categoria, subcategoria, marca_normalizada, precio_min, precio_max
        )
        cls._agregar_filtros_atributos(clauses, params, atributos)
        cls._agregar_filtros_tipo_producto(clauses, params, atributos)
        cls._agregar_exclusion_marca(clauses, params, atributos)

        direccion = "DESC" if (opciones.orden_precio or "asc").lower() == "desc" else "ASC"
        order_parts.append(f"precio_bob {direccion}")
        sql = (
            f"SELECT * FROM productos WHERE {' AND '.join(clauses)} "
            f"ORDER BY {', '.join(order_parts)} LIMIT :limite"
        )
        return sql, params

    @staticmethod
    def _agregar_flags_basicos(
        clauses: list, solo_con_stock: bool, solo_en_oferta: bool
    ) -> None:
        if solo_con_stock:
            clauses.append("stock > 0")
        if solo_en_oferta:
            clauses.append(
                "precio_anterior_bob IS NOT NULL AND precio_anterior_bob > precio_bob"
            )

    @classmethod
    def _agregar_clausula_fulltext(
        cls,
        clauses: list,
        params: dict,
        order_parts: list,
        query_normalizada: str,
    ) -> None:
        q_boolean = cls.tokens_boolean(query_normalizada) if query_normalizada else ""
        if not q_boolean:
            return
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

    @staticmethod
    def _agregar_filtros_jerarquia(
        clauses: list,
        params: dict,
        categoria: Optional[str],
        subcategoria: Optional[str],
        marca_normalizada: Optional[str],
        precio_min: Optional[float],
        precio_max: Optional[float],
    ) -> None:
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
    def _agregar_exclusion_nombre(
        clauses: list, params: dict, nombre_excluye: Optional[list[str]]
    ) -> None:
        """Excluye productos cuyo nombre_norm contenga alguna de las keywords.
        Usado para separar 'reloj de pared' cuando el cliente pide 'reloj'
        a secas: el catalogo no distingue subcategorias finas, pero el
        nombre si — atmosphera reloj pared d30 contiene 'pared'."""
        if not nombre_excluye:
            return
        for i, kw in enumerate(nombre_excluye):
            kw_norm = kw.strip().lower()
            if not kw_norm:
                continue
            key = f"exn{i}"
            clauses.append(f"nombre_norm NOT LIKE :{key}")
            params[key] = f"%{kw_norm}%"

    @staticmethod
    def _agregar_filtro_pulgadas(
        clauses: list, params: dict, a: FiltrosAtributos
    ) -> None:
        """Tolerancia de +/-0.5 en pulgadas exactas: '55 pulgadas' acepta 55.0–55.5."""
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

    @classmethod
    def _agregar_filtros_atributos(
        cls, clauses: list, params: dict, a: FiltrosAtributos
    ) -> None:
        """Anade WHERE sobre columnas estructuradas (capacidades, especificaciones)."""
        cls._agregar_filtro_pulgadas(clauses, params, a)
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
        if a.gpu_dedicada:
            clauses.append(
                "(gpu IS NOT NULL AND gpu != '' "
                "OR nombre_norm LIKE '%rtx%' OR nombre_norm LIKE '%gtx%' "
                "OR nombre_norm LIKE '%geforce%' OR nombre_norm LIKE '%nvidia%' "
                "OR nombre_norm LIKE '%radeon rx%')"
            )
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
        if a.refresh_hz_min is not None:
            clauses.append("refresh_hz >= :hz_min")
            params["hz_min"] = a.refresh_hz_min
        cls._agregar_filtros_smartphone(clauses, params, a)
        cls._agregar_filtros_garantia_so(clauses, params, a)
        cls._agregar_filtros_comerciales(clauses, params, a)
        cls._agregar_filtros_categorica(clauses, params, a)
        cls._agregar_filtros_atributos_json(clauses, params, a)

    @staticmethod
    def _agregar_filtros_smartphone(
        clauses: list, params: dict, a: FiltrosAtributos
    ) -> None:
        """Filtros típicos de celulares y power banks: batería, cámaras, 5G."""
        if a.bateria_mah_min is not None:
            clauses.append("bateria_mah >= :bat_min")
            params["bat_min"] = a.bateria_mah_min
        if a.camara_mp_min is not None:
            clauses.append("camara_mp >= :cmp_min")
            params["cmp_min"] = a.camara_mp_min
        if a.camara_frontal_mp_min is not None:
            clauses.append("camara_frontal_mp >= :cfmp_min")
            params["cfmp_min"] = a.camara_frontal_mp_min
        if a.soporta_5g is not None:
            # 5G es bool estricto: NULL = desconocido = NO pasa cuando se pide.
            clauses.append("soporta_5g = :s5g")
            params["s5g"] = 1 if a.soporta_5g else 0

    @staticmethod
    def _agregar_filtros_garantia_so(
        clauses: list, params: dict, a: FiltrosAtributos
    ) -> None:
        """Filtros de sistema operativo (string match), garantía mínima y modelo."""
        if a.sistema_operativo:
            clauses.append("LOWER(sistema_operativo) = :so")
            params["so"] = a.sistema_operativo.lower()
        if a.meses_garantia_min is not None:
            clauses.append("meses_garantia >= :gar_min")
            params["gar_min"] = a.meses_garantia_min
        if a.modelo:
            clauses.append("LOWER(modelo) LIKE :mod")
            params["mod"] = f"%{a.modelo.lower()}%"

    @staticmethod
    def _agregar_filtros_comerciales(
        clauses: list, params: dict, a: FiltrosAtributos
    ) -> None:
        """Filtros sobre estado comercial: descuento, stock mínimo."""
        if a.tiene_descuento is True:
            clauses.append(
                "precio_anterior_bob IS NOT NULL AND precio_anterior_bob > precio_bob"
            )
        elif a.tiene_descuento is False:
            clauses.append(
                "(precio_anterior_bob IS NULL OR precio_anterior_bob <= precio_bob)"
            )
        if a.descuento_pct_min is not None:
            # (anterior - actual) / anterior * 100 >= pct  ⇒  anterior * (1 - pct/100) >= actual
            clauses.append(
                "precio_anterior_bob IS NOT NULL "
                "AND precio_anterior_bob * (1 - :dpct/100) >= precio_bob"
            )
            params["dpct"] = a.descuento_pct_min
        if a.stock_min is not None:
            clauses.append("stock >= :stock_min")
            params["stock_min"] = a.stock_min

    # Single source of truth: el mapeo de booleanos vive en ValidadorFiltrosDuros.
    # SQL y validador post-fetch comparten el mismo catálogo de keywords.
    @classmethod
    def _atributos_boolean_catalogo(cls) -> tuple:
        # Import lazy para evitar ciclo (validador no debe importar SQL).
        # 5 niveles: sql/ → mariadb/ → persistence/ → infrastructure/ → app/
        from .....application.chat.validador_filtros_duros import ValidadorFiltrosDuros
        return ValidadorFiltrosDuros._ATRIBUTOS_BOOLEANOS

    @classmethod
    def _agregar_filtros_categorica(
        cls, clauses: list, params: dict, a: FiltrosAtributos
    ) -> None:
        """Filtros categóricos textuales que matchean en atributos_texto / caracteristicas."""
        cls._agregar_text_filter(clauses, params, "ip_rating", a.ip_rating, "ipr")
        cls._agregar_text_filter(
            clauses, params, "eficiencia_energetica", a.eficiencia_energetica, "efe",
            valor_transform=lambda v: f"eficiencia: {v.lower()}",
        )
        cls._agregar_text_filter(
            clauses, params, "tipo_combustible", a.tipo_combustible, "comb",
            extra_keywords=lambda v: cls._sinonimos_combustible(v),
        )
        cls._agregar_text_filter(
            clauses, params, "tipo_carga_lavadora", a.tipo_carga_lavadora, "carga",
            valor_transform=lambda v: f"carga {v.lower()}",
        )
        cls._agregar_text_filter(
            clauses, params, "wifi_version", a.wifi_version, "wifv",
        )
        if a.frecuencia_rpm_min is not None:
            # rpm sólo está en atributos_texto. LIKE numérico es frágil; aplicamos
            # un piso conservador: el texto debe contener un número >= valor pedido.
            # Como no podemos comparar números con LIKE, dejamos esto como hint
            # (ValidadorFiltrosDuros lo cachea de p.atributos cuando puede).
            cls._agregar_minimo_numerico(
                clauses, params, "rpm", a.frecuencia_rpm_min, "rpm_min"
            )
        if a.bluetooth_version_min is not None:
            cls._agregar_minimo_numerico(
                clauses, params, "bluetooth", a.bluetooth_version_min, "btv_min"
            )
        if a.hdmi_version_min is not None:
            cls._agregar_minimo_numerico(
                clauses, params, "hdmi", a.hdmi_version_min, "hdmiv_min"
            )
        if a.hdmi_puertos_min is not None:
            cls._agregar_minimo_numerico(
                clauses, params, "puertos hdmi", a.hdmi_puertos_min, "hdmip_min"
            )
        if a.usb_puertos_min is not None:
            cls._agregar_minimo_numerico(
                clauses, params, "puertos usb", a.usb_puertos_min, "usbp_min"
            )
        if a.carga_rapida_w_min is not None:
            cls._agregar_minimo_numerico(
                clauses, params, "carga rapida", a.carga_rapida_w_min, "cr_min"
            )

    @staticmethod
    def _sinonimos_combustible(valor: str) -> list[str]:
        equivalencias = {
            "gas": ["gas", "glp", "gn"],
            "electrico": ["electrico", "eléctrico", "electric"],
            "induccion": ["induccion", "inducción", "induction"],
            "mixto": ["mixto", "mixed"],
        }
        return equivalencias.get(valor.lower(), [valor.lower()])

    @staticmethod
    def _agregar_text_filter(
        clauses: list,
        params: dict,
        nombre: str,
        valor: Optional[str],
        clave_param: str,
        valor_transform=None,
        extra_keywords=None,
    ) -> None:
        """Genera OR de LIKE sobre atributos_texto + nombre_norm + descripcion_norm
        para un filtro textual categórico. Si extra_keywords está dado, expande
        con sinónimos."""
        if not valor:
            return
        if extra_keywords:
            keywords = extra_keywords(valor)
        else:
            base = valor_transform(valor) if valor_transform else valor.lower()
            keywords = [base]
        condiciones = []
        for i, kw in enumerate(keywords):
            key = f"{clave_param}{i}"
            condiciones.append(
                f"(LOWER(atributos_texto) LIKE :{key} OR nombre_norm LIKE :{key} "
                f"OR descripcion_norm LIKE :{key})"
            )
            params[key] = f"%{kw.lower()}%"
        clauses.append("(" + " OR ".join(condiciones) + ")")

    @staticmethod
    def _agregar_minimo_numerico(
        clauses: list, params: dict, etiqueta: str, valor: float, key: str
    ) -> None:
        """Para filtros numéricos sobre atributos JSON (rpm, bluetooth_version, etc.)
        donde no hay columna dedicada — usa LIKE con la etiqueta + valor numérico
        como hint. Es laxo: prefiere falsos positivos a falsos negativos. La
        ValidadorFiltrosDuros recorta más fino sobre p.atributos cuando puede."""
        clauses.append(
            f"(LOWER(atributos_texto) LIKE :{key} OR descripcion_norm LIKE :{key})"
        )
        # Buscar la etiqueta seguida de un número >= valor. Como LIKE no compara
        # números, exigimos al menos que el texto mencione la etiqueta. La validación
        # numérica fina ocurre post-SQL en ValidadorFiltrosDuros.
        params[key] = f"%{etiqueta.lower()}%"

    @classmethod
    def _agregar_filtros_atributos_json(
        cls, clauses: list, params: dict, a: FiltrosAtributos
    ) -> None:
        """Aplica los filtros boolean basados en atributos_texto LIKE.

        Cuando el cliente exige un atributo (p.ej. inverter=True), exigimos que
        alguna de las keywords aparezca en atributos_texto, caracteristicas,
        descripcion_norm o nombre_norm. False → no aplicamos filtro (el cliente
        no excluye, solo no lo pide). NULL → ignorado."""
        for filtro_nombre, keywords in cls._atributos_boolean_catalogo():
            valor = getattr(a, filtro_nombre, None)
            if not valor:
                continue
            condiciones = []
            for i, kw in enumerate(keywords):
                key = f"atjs_{filtro_nombre}_{i}"
                condiciones.append(
                    f"(LOWER(atributos_texto) LIKE :{key} OR LOWER(caracteristicas) LIKE :{key} "
                    f"OR descripcion_norm LIKE :{key} OR nombre_norm LIKE :{key})"
                )
                params[key] = f"%{kw.lower()}%"
            clauses.append("(" + " OR ".join(condiciones) + ")")

    @staticmethod
    def _agregar_filtros_tipo_producto(
        clauses: list, params: dict, a: FiltrosAtributos
    ) -> None:
        """Filtros de subtipo (tipo_producto) y vestibilidad (es_vestible).

        tipo_producto_excluye usa NULL-safe NOT IN para que productos sin
        clasificar (NULL) no queden excluidos — cuando el ingestor aun no
        ha poblado el campo todos los rows son NULL y no queremos devolver
        un catalogo vacio."""
        if a.tipo_producto:
            clauses.append("tipo_producto = :tipo_producto")
            params["tipo_producto"] = a.tipo_producto.lower()
        if a.es_vestible is not None:
            clauses.append("es_vestible = :vestible")
            params["vestible"] = 1 if a.es_vestible else 0
        if a.tipo_producto_excluye:
            placeholders = []
            for i, tp in enumerate(a.tipo_producto_excluye):
                key = f"tpe{i}"
                placeholders.append(f":{key}")
                params[key] = tp.lower()
            joined = ", ".join(placeholders)
            clauses.append(
                f"(tipo_producto IS NULL OR tipo_producto NOT IN ({joined}))"
            )

    @staticmethod
    def _agregar_exclusion_marca(
        clauses: list, params: dict, a: FiltrosAtributos
    ) -> None:
        """Excluye marcas que el cliente rechazó explícitamente.
        NULL-safe: si marca_norm es NULL el producto pasa (no lo excluimos
        por no tener dato de marca)."""
        if not a.marca_excluye:
            return
        for i, marca in enumerate(a.marca_excluye):
            key = f"mexn{i}"
            params[key] = f"%{marca.lower()}%"
            clauses.append(f"(marca_norm IS NULL OR marca_norm NOT LIKE :{key})")

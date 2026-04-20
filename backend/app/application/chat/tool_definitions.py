def _tool(name: str, description: str, properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        },
    }


TOOLS_SPEC: list[dict] = [
    _tool(
        "buscar_productos",
        (
            "Busca productos en el catalogo Dismac. Hasta 6 resultados. Combina filtros "
            "(query de texto + categoria + subcategoria + marca + rango de precio en Bs). "
            "Para filtrar por atributos estructurados prefiere los campos dedicados antes "
            "que incrustarlos en `query`: pulgadas (TVs/monitores/laptops), capacidad_gb_min "
            "(almacenamiento celulares/laptops), ram_gb_min (RAM), capacidad_litros_min "
            "(heladeras/hornos), capacidad_kg_min (lavadoras), potencia_w_min/max "
            "(licuadoras/secadores/aspiradoras), procesador (laptops: i3/i5/i7/i9, "
            "ryzen 3/5/7/9, m1-m4), tipo_panel (OLED/QLED/LED), "
            "resolucion (8K/4K/FHD/HD), color."
        ),
        {
            "query": {
                "type": "string",
                "description": (
                    "SOLO el sustantivo o nombre del producto (ej. 'laptop', "
                    "'televisor', 'freidora', 'iphone 15 pro'). PROHIBIDO pasar "
                    "frases conversacionales del cliente: 'tengo presupuesto de "
                    "30000bs', 'cual me conviene', 'no me interesa la marca', "
                    "'asesorame'. Esas senales van como filtros estructurados "
                    "(precio_max, marca) o las infiere el sistema desde el perfil. "
                    "Si el cliente solo dio contexto/preferencias sin nombrar "
                    "producto, omite `query` y usa los otros filtros."
                ),
            },
            "categoria": {"type": "string"},
            "subcategoria": {"type": "string"},
            "marca": {"type": "string"},
            "precio_max": {"type": "number"},
            "precio_min": {"type": "number"},
            "pulgadas": {
                "type": "number",
                "description": "Pulgadas exactas (tolerancia +/-0.5). Ej: 55 para TV de 55\".",
            },
            "pulgadas_min": {"type": "number"},
            "pulgadas_max": {"type": "number"},
            "capacidad_gb_min": {
                "type": "integer",
                "description": "Almacenamiento minimo en GB (celulares, laptops, tablets).",
            },
            "ram_gb_min": {"type": "integer", "description": "RAM minima en GB."},
            "capacidad_litros_min": {
                "type": "number",
                "description": "Capacidad minima en litros (heladeras, hornos, microondas).",
            },
            "capacidad_kg_min": {
                "type": "number",
                "description": "Capacidad minima en kg (lavadoras).",
            },
            "potencia_w_min": {
                "type": "integer",
                "description": "Potencia minima en W (licuadoras, secadores, aspiradoras).",
            },
            "potencia_w_max": {
                "type": "integer",
                "description": "Potencia maxima en W.",
            },
            "procesador": {
                "type": "string",
                "description": "Procesador canonico (laptops/mini-pc). Ej: i3, i5, i7, i9, ryzen 3, ryzen 5, ryzen 7, ryzen 9, m1, m2, m3, m4, celeron, pentium, xeon, snapdragon, mediatek.",
            },
            "tipo_panel": {
                "type": "string",
                "enum": ["OLED", "QLED", "MINILED", "DLED", "LED"],
            },
            "resolucion": {
                "type": "string",
                "enum": ["8K", "4K", "2K", "FHD", "HD"],
            },
            "color": {"type": "string"},
            "es_electrico": {
                "type": "boolean",
                "description": (
                    "True para vehiculos/productos electricos (motocicletas "
                    "electricas, autos electricos). False para combustion. "
                    "Usar cuando el cliente pregunta 'electricas', 'a bateria', "
                    "'sin gasolina'."
                ),
            },
            "solo_con_stock": {"type": "boolean", "default": True},
        },
    ),
    _tool(
        "listar_categorias",
        "Lista todas las categorias disponibles con cantidad de productos activos.",
        {},
    ),
    _tool(
        "ver_producto",
        "Trae detalle completo de un producto por SKU exacto.",
        {"sku": {"type": "string"}},
        required=["sku"],
    ),
    _tool(
        "agregar_al_carrito",
        "Agrega un producto al carrito. Si ya estaba, suma la cantidad.",
        {
            "sku": {"type": "string"},
            "cantidad": {"type": "integer", "default": 1},
        },
        required=["sku"],
    ),
    _tool(
        "quitar_del_carrito",
        "Quita por completo un SKU del carrito del usuario.",
        {"sku": {"type": "string"}},
        required=["sku"],
    ),
    _tool(
        "ver_carrito",
        "Muestra el estado actual del carrito: items, cantidades, subtotales y total en Bs.",
        {},
    ),
    _tool(
        "vaciar_carrito",
        "Elimina todos los items del carrito del usuario.",
        {},
    ),
    _tool(
        "confirmar_orden",
        "Cierra la compra: toma el carrito y crea una orden maestra con su detalle. Requiere nombre del cliente.",
        {
            "cliente_nombre": {"type": "string"},
            "cliente_email": {"type": "string"},
            "cliente_telefono": {"type": "string"},
            "notas": {"type": "string"},
        },
        required=["cliente_nombre"],
    ),
    _tool(
        "ver_ordenes_sesion",
        "Muestra las ordenes previamente creadas en esta misma sesion.",
        {},
    ),
    _tool(
        "comparar_productos",
        "Compara 2-4 SKUs lado a lado (precio, stock, marca, descripcion). Usala "
        "cuando el cliente pida 'comparar', 'diferencia', 'cual es mejor' entre "
        "productos que ya salieron en la conversacion.",
        {
            "skus": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lista de SKUs a comparar (2 a 4).",
            }
        },
        required=["skus"],
    ),
]

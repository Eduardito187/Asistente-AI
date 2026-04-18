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
        "Busca productos en el catalogo Dismac. Hasta 6 resultados. Combina filtros (query de texto + categoria + subcategoria + marca + rango de precio en Bs).",
        {
            "query": {"type": "string"},
            "categoria": {"type": "string"},
            "subcategoria": {"type": "string"},
            "marca": {"type": "string"},
            "precio_max": {"type": "number"},
            "precio_min": {"type": "number"},
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
]

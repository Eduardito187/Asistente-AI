from __future__ import annotations


class ProductoSql:
    """Catalogo SQL del upsert de productos en el ingestor."""

    UPSERT = """
    INSERT INTO productos (
        sku, nombre, descripcion, categoria, subcategoria, marca,
        precio_bob, precio_anterior_bob, stock, imagen_url, url_producto,
        activo, origen,
        nombre_norm, descripcion_norm, marca_norm, categoria_norm,
        pulgadas, capacidad_gb, ram_gb, capacidad_litros, capacidad_kg,
        potencia_w, procesador, color, tipo_panel, resolucion,
        bateria_mah, camara_mp, camara_frontal_mp, soporta_5g,
        sistema_operativo, refresh_hz, gpu,
        updated_at
    ) VALUES (
        :sku, :nombre, :descripcion, :categoria, :subcategoria, :marca,
        :precio_bob, :precio_anterior_bob, :stock, :imagen_url, :url_producto,
        :activo, :origen,
        :nombre_norm, :descripcion_norm, :marca_norm, :categoria_norm,
        :pulgadas, :capacidad_gb, :ram_gb, :capacidad_litros, :capacidad_kg,
        :potencia_w, :procesador, :color, :tipo_panel, :resolucion,
        :bateria_mah, :camara_mp, :camara_frontal_mp, :soporta_5g,
        :sistema_operativo, :refresh_hz, :gpu,
        NOW(6)
    )
    ON DUPLICATE KEY UPDATE
        nombre              = VALUES(nombre),
        descripcion         = VALUES(descripcion),
        categoria           = VALUES(categoria),
        subcategoria        = VALUES(subcategoria),
        marca               = VALUES(marca),
        precio_bob          = VALUES(precio_bob),
        precio_anterior_bob = VALUES(precio_anterior_bob),
        stock               = VALUES(stock),
        imagen_url          = VALUES(imagen_url),
        url_producto        = VALUES(url_producto),
        activo              = VALUES(activo),
        origen              = VALUES(origen),
        nombre_norm         = VALUES(nombre_norm),
        descripcion_norm    = VALUES(descripcion_norm),
        marca_norm          = VALUES(marca_norm),
        categoria_norm      = VALUES(categoria_norm),
        pulgadas            = VALUES(pulgadas),
        capacidad_gb        = VALUES(capacidad_gb),
        ram_gb              = VALUES(ram_gb),
        capacidad_litros    = VALUES(capacidad_litros),
        capacidad_kg        = VALUES(capacidad_kg),
        potencia_w          = VALUES(potencia_w),
        procesador          = VALUES(procesador),
        color               = VALUES(color),
        tipo_panel          = VALUES(tipo_panel),
        resolucion          = VALUES(resolucion),
        bateria_mah         = VALUES(bateria_mah),
        camara_mp           = VALUES(camara_mp),
        camara_frontal_mp   = VALUES(camara_frontal_mp),
        soporta_5g          = VALUES(soporta_5g),
        sistema_operativo   = VALUES(sistema_operativo),
        refresh_hz          = VALUES(refresh_hz),
        gpu                 = VALUES(gpu),
        updated_at          = NOW(6)
    """

    @staticmethod
    def desactivar_faltantes(n: int) -> str:
        placeholders = ", ".join(f":s{i}" for i in range(n))
        return (
            "UPDATE productos SET activo = 0, updated_at = NOW(6) "
            f"WHERE origen = :o AND activo = 1 AND sku NOT IN ({placeholders})"
        )

    # SQL del source adapter MySQL (lectura del ERP origen)
    LEER_ERP = (
        "SELECT p.sku, p.nombre, p.descripcion, c.nombre AS categoria, m.nombre AS marca, "
        "p.precio_bob, p.precio_anterior_bob, p.stock, p.imagen_url, p.activo "
        "FROM productos p "
        "LEFT JOIN categorias c ON c.id = p.categoria_id "
        "LEFT JOIN marcas m     ON m.id = p.marca_id"
    )

from __future__ import annotations


class PerfilSesionSql:
    """Catalogo SQL del agregado PerfilSesion."""

    POR_ID = (
        "SELECT sesion_id, presupuesto_max, marca_preferida, categoria_foco, "
        "subcategoria_foco, sku_foco, genero_declarado, desired_tier, "
        "uso_declarado, pulgadas, tipo_panel, resolucion, ram_gb_min, gpu_dedicada, "
        "ssd_gb_min, nombre_excluye_acum, presupuesto_ideal, "
        "ultimos_skus_mostrados, precio_min_mostrado, precio_max_mostrado, "
        "alternativa_ofrecida, updated_at "
        "FROM perfiles_sesion WHERE sesion_id = :sid"
    )

    REGISTRAR_ALTERNATIVA = (
        "INSERT INTO perfiles_sesion (sesion_id, alternativa_ofrecida) "
        "VALUES (:sid, :alt) "
        "ON DUPLICATE KEY UPDATE alternativa_ofrecida = VALUES(alternativa_ofrecida)"
    )

    UPSERT = (
        "INSERT INTO perfiles_sesion "
        "(sesion_id, presupuesto_max, marca_preferida, categoria_foco, subcategoria_foco, "
        " sku_foco, genero_declarado, desired_tier, uso_declarado, pulgadas, tipo_panel, "
        " resolucion, ram_gb_min, gpu_dedicada, ssd_gb_min, nombre_excluye_acum, presupuesto_ideal) "
        "VALUES (:sid, :pmax, :marca, :cat, :subcat, :sku, :gen, :tier, :uso, :pulg, "
        "        :panel, :res, :ram, :gpu, :ssd, :excluye, :pideal) "
        "ON DUPLICATE KEY UPDATE "
        "presupuesto_max   = COALESCE(VALUES(presupuesto_max),   presupuesto_max), "
        "marca_preferida   = COALESCE(VALUES(marca_preferida),   marca_preferida), "
        "categoria_foco    = COALESCE(VALUES(categoria_foco),    categoria_foco), "
        "subcategoria_foco = COALESCE(VALUES(subcategoria_foco), subcategoria_foco), "
        "sku_foco          = COALESCE(VALUES(sku_foco),          sku_foco), "
        "genero_declarado  = COALESCE(VALUES(genero_declarado),  genero_declarado), "
        "desired_tier      = COALESCE(VALUES(desired_tier),      desired_tier), "
        "uso_declarado     = COALESCE(VALUES(uso_declarado),     uso_declarado), "
        "pulgadas          = COALESCE(VALUES(pulgadas),          pulgadas), "
        "tipo_panel        = COALESCE(VALUES(tipo_panel),        tipo_panel), "
        "resolucion        = COALESCE(VALUES(resolucion),        resolucion), "
        "ram_gb_min        = COALESCE(VALUES(ram_gb_min),        ram_gb_min), "
        "gpu_dedicada      = COALESCE(VALUES(gpu_dedicada),      gpu_dedicada), "
        "ssd_gb_min        = COALESCE(VALUES(ssd_gb_min),        ssd_gb_min), "
        "presupuesto_ideal = COALESCE(VALUES(presupuesto_ideal), presupuesto_ideal), "
        "nombre_excluye_acum = IF("
        "  VALUES(nombre_excluye_acum) IS NOT NULL, "
        "  IF(nombre_excluye_acum IS NULL, VALUES(nombre_excluye_acum), "
        "     CONCAT(nombre_excluye_acum, ',', VALUES(nombre_excluye_acum))), "
        "  nombre_excluye_acum)"
    )

    REGISTRAR_TURNO = (
        "INSERT INTO perfiles_sesion "
        "(sesion_id, ultimos_skus_mostrados, precio_min_mostrado, precio_max_mostrado) "
        "VALUES (:sid, :skus, :pmin, :pmax) "
        "ON DUPLICATE KEY UPDATE "
        "ultimos_skus_mostrados = VALUES(ultimos_skus_mostrados), "
        "precio_min_mostrado    = VALUES(precio_min_mostrado), "
        "precio_max_mostrado    = VALUES(precio_max_mostrado)"
    )

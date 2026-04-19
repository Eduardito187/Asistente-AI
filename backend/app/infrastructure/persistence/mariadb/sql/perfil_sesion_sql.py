from __future__ import annotations


class PerfilSesionSql:
    """Catalogo SQL del agregado PerfilSesion."""

    POR_ID = (
        "SELECT sesion_id, presupuesto_max, marca_preferida, categoria_foco, "
        "uso_declarado, pulgadas, tipo_panel, resolucion, "
        "ultimos_skus_mostrados, precio_min_mostrado, precio_max_mostrado, "
        "updated_at "
        "FROM perfiles_sesion WHERE sesion_id = :sid"
    )

    UPSERT = (
        "INSERT INTO perfiles_sesion "
        "(sesion_id, presupuesto_max, marca_preferida, categoria_foco, uso_declarado, "
        " pulgadas, tipo_panel, resolucion) "
        "VALUES (:sid, :pmax, :marca, :cat, :uso, :pulg, :panel, :res) "
        "ON DUPLICATE KEY UPDATE "
        "presupuesto_max = COALESCE(VALUES(presupuesto_max), presupuesto_max), "
        "marca_preferida = COALESCE(VALUES(marca_preferida), marca_preferida), "
        "categoria_foco  = COALESCE(VALUES(categoria_foco),  categoria_foco), "
        "uso_declarado   = COALESCE(VALUES(uso_declarado),   uso_declarado), "
        "pulgadas        = COALESCE(VALUES(pulgadas),        pulgadas), "
        "tipo_panel      = COALESCE(VALUES(tipo_panel),      tipo_panel), "
        "resolucion      = COALESCE(VALUES(resolucion),      resolucion)"
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

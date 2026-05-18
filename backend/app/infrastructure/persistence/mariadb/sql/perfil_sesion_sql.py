from __future__ import annotations


class PerfilSesionSql:
    """Catalogo SQL del agregado PerfilSesion."""

    POR_ID = (
        "SELECT sesion_id, presupuesto_max, marca_preferida, categoria_foco, "
        "subcategoria_foco, sku_foco, genero_declarado, desired_tier, "
        "uso_declarado, pulgadas, tipo_panel, resolucion, ram_gb_min, gpu_dedicada, "
        "ssd_gb_min, capacidad_litros_min, nombre_excluye_acum, presupuesto_ideal, "
        "presupuesto_min_buscado, frustracion_count, "
        "ultimos_skus_mostrados, precio_min_mostrado, precio_max_mostrado, "
        "alternativa_ofrecida, ciudad_sesion, updated_at, notas_usuario, "
        "refresh_hz_min, bateria_mah_min, camara_mp_min, soporta_5g, sistema_operativo, "
        "capacidad_kg_min, potencia_w_min, inverter, no_frost, smart_tv, "
        "bluetooth_incluido, nfc, usb_c, hdmi_2_1 "
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
        " resolucion, ram_gb_min, gpu_dedicada, ssd_gb_min, capacidad_litros_min, "
        " nombre_excluye_acum, presupuesto_ideal, presupuesto_min_buscado, frustracion_count, "
        " ciudad_sesion, notas_usuario, refresh_hz_min, bateria_mah_min, camara_mp_min, "
        " soporta_5g, sistema_operativo, capacidad_kg_min, potencia_w_min, inverter, "
        " no_frost, smart_tv, bluetooth_incluido, nfc, usb_c, hdmi_2_1) "
        "VALUES (:sid, :pmax, :marca, :cat, :subcat, :sku, :gen, :tier, :uso, :pulg, "
        "        :panel, :res, :ram, :gpu, :ssd, :litros_min, :excluye, :pideal, "
        "        :pmin_buscado, :frust, :ciudad, :notas, :hz_min, :bat_min, :cam_min, "
        "        :s5g, :so, :kg_min, :pw_min, :inverter, :no_frost, :smart_tv, "
        "        :bluetooth, :nfc, :usb_c, :hdmi_2_1) "
        "ON DUPLICATE KEY UPDATE "
        "presupuesto_max      = COALESCE(VALUES(presupuesto_max),      presupuesto_max), "
        "marca_preferida      = COALESCE(VALUES(marca_preferida),      marca_preferida), "
        "categoria_foco       = COALESCE(VALUES(categoria_foco),       categoria_foco), "
        "subcategoria_foco    = COALESCE(VALUES(subcategoria_foco),    subcategoria_foco), "
        "sku_foco             = COALESCE(VALUES(sku_foco),             sku_foco), "
        "genero_declarado     = COALESCE(VALUES(genero_declarado),     genero_declarado), "
        "desired_tier         = COALESCE(VALUES(desired_tier),         desired_tier), "
        "uso_declarado        = COALESCE(VALUES(uso_declarado),        uso_declarado), "
        "pulgadas             = COALESCE(VALUES(pulgadas),             pulgadas), "
        "tipo_panel           = COALESCE(VALUES(tipo_panel),           tipo_panel), "
        "resolucion           = COALESCE(VALUES(resolucion),           resolucion), "
        "ram_gb_min           = COALESCE(VALUES(ram_gb_min),           ram_gb_min), "
        "gpu_dedicada         = COALESCE(VALUES(gpu_dedicada),         gpu_dedicada), "
        "ssd_gb_min           = COALESCE(VALUES(ssd_gb_min),           ssd_gb_min), "
        "capacidad_litros_min = COALESCE(VALUES(capacidad_litros_min), capacidad_litros_min), "
        "presupuesto_ideal    = COALESCE(VALUES(presupuesto_ideal),    presupuesto_ideal), "
        "presupuesto_min_buscado = COALESCE(VALUES(presupuesto_min_buscado), presupuesto_min_buscado), "
        "ciudad_sesion        = COALESCE(VALUES(ciudad_sesion),        ciudad_sesion), "
        "refresh_hz_min       = COALESCE(VALUES(refresh_hz_min),       refresh_hz_min), "
        "bateria_mah_min      = COALESCE(VALUES(bateria_mah_min),      bateria_mah_min), "
        "camara_mp_min        = COALESCE(VALUES(camara_mp_min),        camara_mp_min), "
        "soporta_5g           = COALESCE(VALUES(soporta_5g),           soporta_5g), "
        "sistema_operativo    = COALESCE(VALUES(sistema_operativo),    sistema_operativo), "
        "capacidad_kg_min     = COALESCE(VALUES(capacidad_kg_min),     capacidad_kg_min), "
        "potencia_w_min       = COALESCE(VALUES(potencia_w_min),       potencia_w_min), "
        "inverter             = COALESCE(VALUES(inverter),             inverter), "
        "no_frost             = COALESCE(VALUES(no_frost),             no_frost), "
        "smart_tv             = COALESCE(VALUES(smart_tv),             smart_tv), "
        "bluetooth_incluido   = COALESCE(VALUES(bluetooth_incluido),   bluetooth_incluido), "
        "nfc                  = COALESCE(VALUES(nfc),                  nfc), "
        "usb_c                = COALESCE(VALUES(usb_c),                usb_c), "
        "hdmi_2_1             = COALESCE(VALUES(hdmi_2_1),             hdmi_2_1), "
        # notas_usuario: ACUMULA (append) en lugar de pisar. NULL nuevo = sin cambio.
        "notas_usuario = IF("
        "  VALUES(notas_usuario) IS NOT NULL, "
        "  IF(notas_usuario IS NULL, VALUES(notas_usuario), "
        "     LEFT(CONCAT(notas_usuario, '\\n', VALUES(notas_usuario)), 2000)), "
        "  notas_usuario), "
        # frustracion_count: SUMA acumulativa (no pick). VALUES(...) trae el delta.
        "frustracion_count = COALESCE(frustracion_count, 0) + COALESCE(VALUES(frustracion_count), 0), "
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

    # Limpieza PARCIAL: solo atributos del dominio DIGITAL (al cambiar a linea_blanca/TV).
    # Borra también marca y presupuesto porque son altamente contextuales por dominio.
    LIMPIAR_DOMINIO_DIGITAL = (
        "UPDATE perfiles_sesion SET "
        "  ram_gb_min           = NULL, "
        "  ssd_gb_min           = NULL, "
        "  gpu_dedicada         = NULL, "
        "  refresh_hz_min       = NULL, "
        "  bateria_mah_min      = NULL, "
        "  camara_mp_min        = NULL, "
        "  soporta_5g           = NULL, "
        "  sistema_operativo    = NULL, "
        "  nfc                  = NULL, "
        "  usb_c                = NULL, "
        "  pulgadas             = NULL, "
        "  tipo_panel           = NULL, "
        "  resolucion           = NULL, "
        "  hdmi_2_1             = NULL, "
        "  smart_tv             = NULL, "
        "  bluetooth_incluido   = NULL, "
        "  marca_preferida      = NULL, "
        "  presupuesto_max      = NULL, "
        "  presupuesto_ideal    = NULL, "
        "  presupuesto_min_buscado = NULL, "
        "  desired_tier         = NULL, "
        "  uso_declarado        = NULL, "
        "  sku_foco             = NULL, "
        "  subcategoria_foco    = NULL "
        "WHERE sesion_id = :sid"
    )

    # Limpieza PARCIAL: solo atributos del dominio LINEA_BLANCA (al cambiar a digital/TV).
    LIMPIAR_DOMINIO_LINEA_BLANCA = (
        "UPDATE perfiles_sesion SET "
        "  capacidad_litros_min = NULL, "
        "  capacidad_kg_min     = NULL, "
        "  potencia_w_min       = NULL, "
        "  inverter             = NULL, "
        "  no_frost             = NULL, "
        "  smart_tv             = NULL, "
        "  marca_preferida      = NULL, "
        "  presupuesto_max      = NULL, "
        "  presupuesto_ideal    = NULL, "
        "  presupuesto_min_buscado = NULL, "
        "  desired_tier         = NULL, "
        "  uso_declarado        = NULL, "
        "  sku_foco             = NULL, "
        "  subcategoria_foco    = NULL "
        "WHERE sesion_id = :sid"
    )

    # Limpieza PARCIAL: atributos del dominio TV (al cambiar a otro dominio).
    LIMPIAR_DOMINIO_TV = (
        "UPDATE perfiles_sesion SET "
        "  pulgadas             = NULL, "
        "  tipo_panel           = NULL, "
        "  resolucion           = NULL, "
        "  hdmi_2_1             = NULL, "
        "  smart_tv             = NULL, "
        "  bluetooth_incluido   = NULL, "
        "  marca_preferida      = NULL, "
        "  presupuesto_max      = NULL, "
        "  presupuesto_ideal    = NULL, "
        "  presupuesto_min_buscado = NULL, "
        "  desired_tier         = NULL, "
        "  uso_declarado        = NULL, "
        "  sku_foco             = NULL, "
        "  subcategoria_foco    = NULL "
        "WHERE sesion_id = :sid"
    )

    OBTENER_CONTEXTO_DOMINIO = (
        "SELECT dominio_contexto FROM perfiles_sesion WHERE sesion_id = :sid"
    )

    GUARDAR_CONTEXTO_DOMINIO = (
        "INSERT INTO perfiles_sesion (sesion_id, dominio_contexto) "
        "VALUES (:sid, :ctx) "
        "ON DUPLICATE KEY UPDATE dominio_contexto = VALUES(dominio_contexto)"
    )

    LIMPIAR_BUSQUEDA = (
        "UPDATE perfiles_sesion SET "
        "  categoria_foco       = NULL, "
        "  subcategoria_foco    = NULL, "
        "  marca_preferida      = NULL, "
        "  sku_foco             = NULL, "
        "  uso_declarado        = NULL, "
        "  desired_tier         = NULL, "
        "  presupuesto_max      = NULL, "
        "  presupuesto_ideal    = NULL, "
        "  presupuesto_min_buscado = NULL, "
        "  pulgadas             = NULL, "
        "  tipo_panel           = NULL, "
        "  resolucion           = NULL, "
        "  ram_gb_min           = NULL, "
        "  gpu_dedicada         = NULL, "
        "  ssd_gb_min           = NULL, "
        "  capacidad_litros_min = NULL, "
        "  alternativa_ofrecida = NULL, "
        "  nombre_excluye_acum  = NULL, "
        "  ultimos_skus_mostrados = NULL, "
        "  refresh_hz_min       = NULL, "
        "  bateria_mah_min      = NULL, "
        "  camara_mp_min        = NULL, "
        "  soporta_5g           = NULL, "
        "  sistema_operativo    = NULL, "
        "  capacidad_kg_min     = NULL, "
        "  potencia_w_min       = NULL, "
        "  inverter             = NULL, "
        "  no_frost             = NULL, "
        "  smart_tv             = NULL, "
        "  bluetooth_incluido   = NULL, "
        "  nfc                  = NULL, "
        "  usb_c                = NULL, "
        "  hdmi_2_1             = NULL "
        "WHERE sesion_id = :sid"
    )

    # Limpieza mínima: solo presupuesto + marca huérfanos (cuando categoria_foco
    # era NULL al llegar a un nuevo dominio conocido, sin cambio de dominio
    # explícito).
    LIMPIAR_PRESUPUESTO_Y_MARCA = (
        "UPDATE perfiles_sesion SET "
        "  presupuesto_max         = NULL, "
        "  presupuesto_ideal       = NULL, "
        "  presupuesto_min_buscado = NULL, "
        "  marca_preferida         = NULL "
        "WHERE sesion_id = :sid"
    )

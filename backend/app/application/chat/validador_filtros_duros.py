from __future__ import annotations

import logging

log = logging.getLogger("validador_filtros_duros")


class ValidadorFiltrosDuros:
    """Valida que un producto candidato cumpla las restricciones obligatorias
    del turno (categoria, rango de precio, pulgadas, atributos estructurados).

    Unica responsabilidad: decidir si un Producto pasa o no el filtro duro.
    Se usa para cortar candidatos semanticos que aparecen fuera del contexto
    comercial (ej: power bank de 30000mAh cuando el cliente busca TV)."""

    _MINIMOS = (
        ("capacidad_gb_min", "capacidad_gb"),
        ("ram_gb_min", "ram_gb"),
        ("capacidad_litros_min", "capacidad_litros"),
        ("capacidad_kg_min", "capacidad_kg"),
        ("potencia_w_min", "potencia_w"),
        ("refresh_hz_min", "refresh_hz"),
        ("bateria_mah_min", "bateria_mah"),
        ("camara_mp_min", "camara_mp"),
        ("camara_frontal_mp_min", "camara_frontal_mp"),
        ("meses_garantia_min", "meses_garantia"),
    )
    _IGUALES = (
        ("procesador", "procesador"),
        ("tipo_panel", "tipo_panel"),
        ("resolucion", "resolucion"),
        ("color", "color"),
        ("sistema_operativo", "sistema_operativo"),
    )
    _BOOLEANOS_ESTRICTOS = (
        # Cuando el cliente exige True, el producto con NULL queda fuera
        # (desconocido != confirmado).
        ("soporta_5g", "soporta_5g"),
    )
    _TOLERANCIA_PULGADAS = 0.5

    _REGLAS = (
        ("_cumple_textuales", "categoria_marca_subcat_mismatch"),
        ("_cumple_precio", "precio_fuera_rango"),
        ("_cumple_pulgadas", "pulgadas_fuera_rango"),
        ("_cumple_minimos", "spec_minimo_no_cumplido"),
        ("_cumple_potencia_max", "potencia_excede_max"),
        ("_cumple_iguales", "atributo_no_coincide"),
        ("_cumple_es_electrico", "es_electrico_no_coincide"),
        ("_cumple_nombre_excluye", "nombre_excluido"),
        ("_cumple_tipo_producto_excluye", "tipo_producto_excluido"),
        ("_cumple_gpu_dedicada", "gpu_dedicada_no_confirmada"),
        ("_cumple_marca_excluye", "marca_excluida"),
        ("_cumple_booleanos_estrictos", "booleano_estricto_no_coincide"),
        ("_cumple_atributos_json", "atributo_json_no_coincide"),
        ("_cumple_descuento", "descuento_no_coincide"),
        ("_cumple_stock_min", "stock_insuficiente"),
    )

    @classmethod
    def cumple(cls, p, filtros: dict) -> bool:
        razon = cls.razon_descarte(p, filtros)
        if razon is not None:
            log.info(
                "discard sku=%s reason=%s nombre=%s",
                str(getattr(p, "sku", "?")),
                razon,
                (getattr(p, "nombre", "") or "")[:60],
            )
            return False
        return True

    @classmethod
    def razon_descarte(cls, p, filtros: dict) -> str | None:
        for metodo, codigo in cls._REGLAS:
            if not getattr(cls, metodo)(p, filtros):
                return codigo
        return None

    @staticmethod
    def _cumple_tipo_producto_excluye(p, filtros: dict) -> bool:
        """Filtra candidatos semánticos cuyo tipo_producto esté en la lista de
        exclusión. NULL-safe: si el producto no tiene tipo_producto clasificado
        pasa siempre — solo se rechaza cuando hay un valor explícito excluido."""
        excluir = filtros.get("tipo_producto_excluye")
        if not excluir:
            return True
        tp = getattr(p, "tipo_producto", None)
        if tp is None:
            return True
        return tp.lower() not in {e.lower() for e in excluir}

    @staticmethod
    def _cumple_nombre_excluye(p, filtros: dict) -> bool:
        """Excluye productos cuyo nombre contiene alguna keyword vetada por
        el cliente ('no para pared', 'reloj' => no pared/mural). Los candidatos
        semanticos se filtran aqui igual que los fulltext."""
        excluir = filtros.get("nombre_excluye")
        if not excluir:
            return True
        nombre = (getattr(p, "nombre", None) or "").lower()
        return not any(kw.lower() in nombre for kw in excluir if kw)

    @staticmethod
    def _cumple_textuales(p, filtros: dict) -> bool:
        categoria = filtros.get("categoria")
        if categoria and categoria.lower() not in (p.categoria or "").lower():
            return False
        subcategoria = filtros.get("subcategoria")
        if subcategoria and subcategoria.lower() not in (p.subcategoria or "").lower():
            return False
        marca = filtros.get("marca")
        if marca and marca.lower() not in (p.marca or "").lower():
            return False
        return True

    @staticmethod
    def _cumple_precio(p, filtros: dict) -> bool:
        precio = float(p.precio.monto)
        precio_min = filtros.get("precio_min")
        if precio_min is not None and precio < precio_min:
            return False
        precio_max = filtros.get("precio_max")
        if precio_max is not None and precio > precio_max:
            return False
        return True

    @classmethod
    def _cumple_pulgadas(cls, p, filtros: dict) -> bool:
        pulgadas = filtros.get("pulgadas")
        if pulgadas is not None and (p.pulgadas is None or abs(p.pulgadas - pulgadas) > cls._TOLERANCIA_PULGADAS):
            return False
        pulgadas_min = filtros.get("pulgadas_min")
        if pulgadas_min is not None and (p.pulgadas is None or p.pulgadas < pulgadas_min):
            return False
        pulgadas_max = filtros.get("pulgadas_max")
        if pulgadas_max is not None and (p.pulgadas is None or p.pulgadas > pulgadas_max):
            return False
        return True

    @classmethod
    def _cumple_minimos(cls, p, filtros: dict) -> bool:
        for campo, atributo in cls._MINIMOS:
            minimo = filtros.get(campo)
            if minimo is None:
                continue
            valor = getattr(p, atributo, None)
            if valor is None or valor < minimo:
                return False
        return True

    @staticmethod
    def _cumple_potencia_max(p, filtros: dict) -> bool:
        potencia_max = filtros.get("potencia_w_max")
        if potencia_max is None:
            return True
        return p.potencia_w is not None and p.potencia_w <= potencia_max

    @classmethod
    def _cumple_iguales(cls, p, filtros: dict) -> bool:
        for campo, atributo in cls._IGUALES:
            esperado = filtros.get(campo)
            if not esperado:
                continue
            actual = (getattr(p, atributo, None) or "").lower()
            if actual != esperado.lower():
                return False
        return True

    @staticmethod
    def _cumple_es_electrico(p, filtros: dict) -> bool:
        """Booleano estricto: si el filtro pide electrico=True/False, un producto
        con es_electrico=None queda fuera (desconocido != confirmado)."""
        esperado = filtros.get("es_electrico")
        if esperado is None:
            return True
        return p.es_electrico is not None and bool(p.es_electrico) == bool(esperado)

    @staticmethod
    def _cumple_gpu_dedicada(p, filtros: dict) -> bool:
        """Si el cliente exige GPU dedicada, solo pasan productos con campo `gpu`
        poblado (nombre de la GPU). NULL = integrada o desconocida = no pasa."""
        if not filtros.get("gpu_dedicada"):
            return True
        return bool(getattr(p, "gpu", None))

    @staticmethod
    def _cumple_marca_excluye(p, filtros: dict) -> bool:
        """Aplica lista de marcas excluidas a candidatos semánticos (el SQL ya
        los filtra vía WHERE; esta validación cubre los extras traídos por
        búsqueda semántica que bypass an el pipeline SQL)."""
        excluir = filtros.get("marca_excluye")
        if not excluir:
            return True
        marca = (getattr(p, "marca", None) or "").lower()
        return marca not in {e.lower() for e in excluir}

    @classmethod
    def _cumple_booleanos_estrictos(cls, p, filtros: dict) -> bool:
        """Para campos boolean estrictos (soporta_5g, etc.): si el filtro pide
        True/False, un producto con None queda fuera (desconocido != confirmado)."""
        for campo, atributo in cls._BOOLEANOS_ESTRICTOS:
            esperado = filtros.get(campo)
            if esperado is None:
                continue
            actual = getattr(p, atributo, None)
            if actual is None or bool(actual) != bool(esperado):
                return False
        return True

    # --- Atributos via JSON / texto plano de la ficha técnica ----------------
    # Mapeo: filtro_bool → tokens que deben aparecer en atributos_texto.
    # Aplicado tanto en SQL (LIKE) como aquí en validación local del Producto
    # (lee p.atributos cuando está cargado, sino p.caracteristicas/descripcion).

    _ATRIBUTOS_BOOLEANOS = (
        # filtro              keywords (al menos 1 debe matchear como sí/incluido)
        ("inverter",                ("inverter",)),
        ("no_frost",                ("no frost", "nofrost")),
        ("anc",                     ("anc", "noise cancel", "cancelacion de ruido", "cancelación de ruido")),
        ("bluetooth_incluido",      ("bluetooth",)),
        ("wifi_incluido",           ("wifi", "wi-fi", "wi fi")),
        ("tactil",                  ("tactil", "táctil", "touch screen", "touchscreen", "pantalla tactil")),
        ("lector_huella",           ("lector de huella", "lector huella", "huella dactilar", "fingerprint")),
        ("dual_sim",                ("dual sim", "doble sim", "dualsim")),
        ("inalambrico",             ("inalambric", "inalámbric", "wireless")),
        ("dolby_atmos",             ("dolby atmos",)),
        ("usb_c",                   ("usb-c", "usb tipo c", "type-c", "tipo c")),
        ("nfc",                     ("nfc",)),
        ("hdmi_2_1",                ("hdmi 2.1", "hdmi2.1")),
        ("hdmi_arc",                ("hdmi arc", "earc")),
        ("dolby_vision",            ("dolby vision",)),
        ("hdr",                     ("hdr",)),
        ("hdr10",                   ("hdr10",)),
        ("smart_tv",                ("smart tv", "smarttv", "android tv", "google tv", "webos", "tizen")),
        ("airfryer",                ("air fryer", "airfryer", "freidora de aire")),
        ("control_remoto",          ("control remoto", "remote control")),
        ("control_voz",             ("control por voz", "asistente de voz", "alexa", "google assistant")),
        ("retroiluminado",          ("retroiluminado", "backlit", "iluminado")),
        ("plegable",                ("plegable", "foldable")),
        ("convertible",             ("convertible", "2 en 1", "2-in-1")),
        ("touchpad",                ("touchpad",)),
        ("teclado_numerico",        ("teclado numerico", "teclado numérico", "numpad")),
        ("camara_web",              ("webcam", "camara web", "cámara web")),
        ("microfono",               ("microfono", "micrófono", "microphone")),
        ("ranura_sd",               ("ranura sd", "lector sd", "tarjeta sd", "microsd")),
        ("hdmi_puerto",             ("hdmi",)),
        ("ethernet",                ("ethernet", "rj45", "rj-45")),
        ("solar",                   ("solar", "panel solar")),
        ("recargable",              ("recargable", "rechargeable")),
        ("portatil",                ("portatil", "portátil", "portable")),
        ("estabilizador",           ("estabilizador", "stabilizer")),
        ("antiderrame",             ("antiderrame", "anti-derrame")),
        ("auto_apagado",            ("auto apagado", "apagado automatico", "apagado automático")),
        ("temporizador",            ("temporizador", "timer")),
        ("display_digital",         ("display digital", "pantalla digital")),
        ("antiadherente",           ("antiadherente", "non-stick")),
        ("multifuncion",            ("multifuncion", "multifunción", "multifunctional")),
        ("turbo",                   ("turbo", "modo turbo")),
        ("eco",                     ("modo eco", "ecomode")),
        ("silencioso",              ("silencioso", "silent")),
        ("ip67",                    ("ip67",)),
        ("ip68",                    ("ip68",)),
        ("ipx4",                    ("ipx4", "ip x4")),
        ("resistente_agua",         ("resistente al agua", "resistencia al agua", "waterproof", "ip6", "ip7", "ip8")),
        ("carga_inalambrica",       ("carga inalambrica", "carga inalámbrica", "wireless charging")),
        ("oled_keyboard",           ("teclado oled",)),
        ("modo_avion",              ("modo avion", "modo avión", "airplane mode")),
        ("gps",                     ("gps",)),
        ("acelerometro",            ("acelerometro", "acelerómetro")),
        ("monitor_cardiaco",        ("monitor cardiaco", "ritmo cardiaco", "heart rate")),
        ("oximetro",                ("oximetro", "oxímetro", "spo2")),
        ("podometro",               ("podometro", "podómetro", "step counter")),
        # --- Smart Home / IoT --------------------------------------------------
        ("alexa_compatible",        ("alexa", "amazon alexa", "compatible alexa")),
        ("google_home_compatible",  ("google home", "google assistant", "compatible google")),
        ("homekit_compatible",      ("homekit", "apple home", "siri")),
        ("matter_compatible",       ("matter compatible", "protocolo matter")),
        ("zigbee",                  ("zigbee",)),
        ("z_wave",                  ("z-wave", "z wave", "zwave")),
        ("ifttt",                   ("ifttt",)),
        ("app_movil",               ("app movil", "app móvil", "aplicacion movil", "controlable por app", "smart app", "app dedicada")),
        ("smart_home",              ("smart home", "domotica", "domótica", "casa inteligente")),
        # --- Salud / Cuidado personal -----------------------------------------
        ("bpa_free",                ("bpa free", "sin bpa", "libre de bpa")),
        ("hipoalergenico",          ("hipoalergenico", "hipoalergénico", "hypoallergenic")),
        ("antibacterial",           ("antibacterial", "antibacteriano", "antimicrobiano")),
        ("antiacaros",              ("antiacaros", "antiácaros", "anti-acaros")),
        ("ionizador",               ("ionizador", "ionic", "iones")),
        ("filtro_hepa",             ("hepa", "filtro hepa")),
        ("filtro_carbon",           ("filtro de carbon", "filtro carbon activado", "carbon activado")),
        ("filtro_uv",               ("filtro uv", "esterilizacion uv", "uv-c", "ultravioleta")),
        ("aromaterapia",            ("aromaterapia", "aceites esenciales", "difusor de aromas")),
        ("cromoterapia",            ("cromoterapia", "luz led colores", "led multicolor")),
        ("monitor_presion",         ("monitor de presion", "tensiometro", "tensiómetro", "presion arterial")),
        ("monitor_glucosa",         ("monitor de glucosa", "glucometro", "glucómetro")),
        ("monitor_temperatura",     ("termometro", "termómetro", "monitor temperatura")),
        ("masajeador",              ("masajeador", "masaje", "masajeo")),
        # --- Seguridad cocina/hogar -------------------------------------------
        ("cierre_infantil",         ("cierre infantil", "child lock", "seguro para niños", "seguro infantil")),
        ("doble_vidrio",            ("doble vidrio", "doble cristal")),
        ("vidrio_templado",         ("vidrio templado", "cristal templado", "tempered glass")),
        ("asa_fria",                ("asa fria", "asa fría", "cool touch")),
        ("antichoque",              ("antichoque", "anti-impacto", "shockproof")),
        ("resistente_calor",        ("resistente al calor", "alta temperatura", "heat resistant")),
        ("apto_lavavajillas",       ("apto lavavajillas", "lavavajillas seguro", "dishwasher safe")),
        ("apto_microondas",         ("apto microondas", "microwave safe", "para microondas")),
        ("apto_horno",              ("apto horno", "oven safe", "para horno")),
        ("apto_induccion",          ("apto induccion", "compatible induccion", "induction ready")),
        ("apto_congelador",         ("apto congelador", "freezer safe", "para congelador")),
        ("detector_humo",           ("detector de humo", "smoke detector")),
        ("sensor_movimiento",       ("sensor de movimiento", "motion sensor", "deteccion de movimiento")),
        ("alarma",                  ("alarma", "sirena", "alarm")),
        # --- Materiales especiales --------------------------------------------
        ("acero_inoxidable",        ("acero inoxidable", "stainless steel", "inox")),
        ("madera_solida",           ("madera solida", "madera maciza", "solid wood")),
        ("bambu",                   ("bambu", "bambú", "bamboo")),
        ("ceramica_material",       ("ceramica", "cerámica", "ceramic")),
        ("silicona_material",       ("silicona", "silicone")),
        ("cuero_real",              ("cuero genuino", "cuero real", "leather", "cuero natural")),
        ("algodon_organico",        ("algodon organico", "algodón orgánico", "organic cotton")),
        ("aluminio_material",       ("aluminio", "aluminum")),
        ("titanio",                 ("titanio", "titanium")),
        ("fibra_carbono",           ("fibra de carbono", "carbon fiber")),
        ("microfibra",              ("microfibra", "microfiber")),
        # --- Funciones electro avanzadas --------------------------------------
        ("auto_limpieza",           ("auto limpieza", "autolimpieza", "self cleaning", "limpieza automatica")),
        ("auto_descongelado",       ("auto descongelado", "frost free", "descongelado automatico")),
        ("diagnostico_inteligente", ("diagnostico inteligente", "smart diagnosis", "auto diagnostico")),
        ("notif_movil",             ("notificacion movil", "notif al telefono", "alerta movil", "smart alert")),
        ("modo_nocturno",           ("modo nocturno", "night mode", "modo noche")),
        ("modo_vacaciones",         ("modo vacaciones", "vacation mode", "holiday mode")),
        ("alarma_puerta",           ("alarma puerta", "alarma de puerta abierta", "door alarm")),
        ("congelacion_rapida",      ("congelacion rapida", "fast freeze", "quick freeze")),
        ("enfriamiento_rapido",     ("enfriamiento rapido", "fast cooling", "quick cool")),
        ("vapor",                   ("vapor", "steam")),
        ("lavado_frio",             ("lavado en frio", "agua fria", "cold wash")),
        ("secado_calor",            ("secado por calor", "secado caliente", "heat dry")),
        ("secado_aire",             ("secado por aire", "air dry")),
        ("iones_negativos",         ("iones negativos", "negative ions")),
        ("ozono",                   ("ozono", "ozonizador", "o3")),
        # --- Pequeños electro -------------------------------------------------
        ("antical",                 ("antical", "anti-cal", "descalcificador")),
        ("antigoteo",               ("antigoteo", "anti-drip", "no drip")),
        ("cable_recogible",         ("cable recogible", "cable retraible", "retractable cable")),
        ("giratorio_360",           ("360 grados", "360°", "giro 360", "rotación completa")),
        ("mango_ergonomico",        ("mango ergonomico", "ergonomic handle")),
        ("desmontable",             ("desmontable", "removable", "removible")),
        ("recipiente_extraible",    ("recipiente extraible", "depósito extraible", "removable container")),
        ("jarra_vidrio",            ("jarra de vidrio", "glass jug")),
        ("jarra_inoxidable",        ("jarra de acero", "jarra inoxidable", "steel jug")),
        # --- Conectividad extra -----------------------------------------------
        ("thunderbolt",             ("thunderbolt",)),
        ("displayport",             ("displayport", "display port")),
        ("mini_jack",               ("mini jack", "jack 3.5", "audio jack")),
        ("triple_camara",           ("triple camara", "triple cámara", "tres camaras", "3 cámaras")),
        ("cuadruple_camara",        ("cuadruple camara", "cuádruple cámara", "cuatro camaras", "4 cámaras")),
        ("camara_macro",            ("camara macro", "lente macro", "macro lens")),
        ("camara_telefoto",         ("telefoto", "telephoto", "lente telefoto")),
        ("camara_ultrawide",        ("ultrawide", "ultra gran angular", "ultra wide")),
        ("vision_nocturna",         ("vision nocturna", "night vision", "modo nocturno")),
        ("ois",                     ("ois", "estabilizacion optica", "optical image stabilization")),
        ("video_4k",                ("graba 4k", "video 4k", "4k video", "grabacion 4k")),
        ("video_8k",                ("video 8k", "8k video", "graba 8k")),
        ("slow_motion",             ("slow motion", "camara lenta", "cámara lenta")),
        # --- Adecuación de uso ------------------------------------------------
        ("para_gaming",             ("gaming", "gamer", "para juegos", "esports")),
        ("para_oficina",            ("para oficina", "uso oficina", "office")),
        ("para_diseno",             ("diseño grafico", "diseño profesional", "graphic design")),
        ("para_streaming",          ("streaming", "para stream", "transmision")),
        ("para_outdoor",            ("outdoor", "exterior", "uso exterior", "intemperie")),
        ("para_viaje",              ("para viaje", "viajero", "travel", "compacto viaje")),
        ("para_bebe",               ("para bebe", "para bebé", "infantil", "niños pequeños", "para niños")),
        ("para_adulto_mayor",       ("adulto mayor", "tercera edad", "geriatrico", "senior")),
        # --- Audio profesional ------------------------------------------------
        ("aptx",                    ("aptx",)),
        ("aptx_hd",                 ("aptx hd", "aptx-hd")),
        ("ldac",                    ("ldac",)),
        ("spatial_audio",           ("spatial audio", "audio espacial")),
        ("bass_boost",              ("bass boost", "refuerzo de graves", "extra bass")),
        ("ecualizador",             ("ecualizador", "equalizer", "eq")),
        ("multipoint",              ("multipoint", "multipunto", "doble dispositivo")),
        ("transparency_mode",       ("transparency mode", "modo transparencia", "modo ambiente")),
        ("hi_res_audio",            ("hi-res audio", "high resolution audio", "audio hi-res")),
        # --- Estética / diseño ------------------------------------------------
        ("bordes_redondeados",      ("bordes redondeados", "rounded edges")),
        ("sin_marco",               ("sin marco", "borderless", "frameless", "infinite display", "marco infinito")),
        ("transparente_diseno",     ("transparente", "transparent")),
        ("diseno_ergonomico",       ("diseño ergonomico", "ergonomic design")),
        ("premium_diseno",          ("acabado premium", "diseño premium", "premium finish", "acabado de lujo")),
        # --- Bicis / movilidad ------------------------------------------------
        ("abs_motos",               ("abs", "frenos abs", "antibloqueo")),
        ("electrico_bici",          ("e-bike", "bici electrica", "bicicleta eléctrica", "bici eléctrica")),
        ("frenos_disco",            ("frenos de disco", "disc brakes", "freno disco")),
        ("suspension_doble",        ("doble suspension", "full suspension", "suspensión completa")),
        ("suspension_delantera",    ("suspension delantera", "horquilla suspension")),
        ("cambios_shimano",         ("shimano", "cambios shimano")),
        # --- Monitores gaming -------------------------------------------------
        ("gsync",                   ("g-sync", "gsync", "nvidia g-sync")),
        ("freesync",                ("freesync", "amd freesync")),
        ("monitor_curvo",           ("curvo", "curved", "pantalla curva")),
        ("pivot_monitor",           ("pivot", "rotacion vertical", "pantalla rotable")),
        ("altura_ajustable",        ("altura ajustable", "height adjustable")),
        ("hub_usb_c",               ("hub usb-c", "usb-c hub", "docking usb-c")),
        # --- Drones / cámaras pro ---------------------------------------------
        ("evita_obstaculos",        ("evita obstaculos", "obstacle avoidance", "deteccion obstaculos")),
        ("retorno_automatico",      ("retorno automatico", "return to home", "rth")),
        ("seguimiento_inteligente", ("active track", "follow me", "seguimiento")),
        # --- Bebés / niños ----------------------------------------------------
        ("educativo",               ("educativo", "educational", "didactico")),
        ("stem",                    ("stem", "ciencia tecnologia", "robotica educativa")),
        # --- Sustentabilidad / certificaciones --------------------------------
        ("energy_star",             ("energy star",)),
        ("reciclable",              ("reciclable", "recyclable", "100% reciclable")),
        ("eco_friendly",            ("eco-friendly", "eco friendly", "amigable con el medio")),
        ("refrigerante_eco",        ("r600a", "r-600a", "r32", "r-32", "refrigerante ecologico")),
        # --- Otros / pago / disponibilidad ------------------------------------
        ("envio_rapido",            ("envio rapido", "envío rápido", "entrega en 24h", "envio express")),
        ("garantia_extendida",      ("garantia extendida", "extended warranty", "garantia adicional")),
        ("manual_incluido",         ("manual incluido", "manual de usuario", "user manual")),
        ("control_app",             ("control desde app", "control via app", "controlable desde aplicacion")),
        ("notif_push",              ("notificaciones push", "push notifications")),
        # ========================================================================
        # MEGA RONDA 3: pensando como comprador real (sinonimos + frases de la calle)
        # ========================================================================
        # --- Atributos blandos ("que no haga X") ------------------------------
        ("ultra_silencioso",        ("ultra silencioso", "casi sin ruido", "<30db", "menos de 30 db", "muy silencioso")),
        ("bajo_consumo",            ("bajo consumo", "ahorra energia", "ahorrador", "low power", "ahorro energetico", "consumo eficiente")),
        ("liviano",                 ("liviano", "ligero", "ultra ligero", "ultraligero", "lightweight", "peso ligero", "poco peso")),
        ("compacto",                ("compacto", "compact", "ahorra espacio", "espacio reducido", "diseño compacto")),
        ("durable",                 ("durable", "durabilidad", "larga vida", "long lasting", "duradero")),
        ("resistente_caidas",       ("resistente a caidas", "anti-caida", "drop proof", "shockproof", "aguanta golpes", "anti golpe")),
        ("resistente_rayones",      ("resistente a rayones", "scratch proof", "anti-rayones", "no se raya")),
        ("anti_oxido",              ("anti oxido", "anti-corrosion", "no se oxida", "rustproof")),
        ("resistente_uv",           ("resistente uv", "uv protection", "proteccion solar", "anti-uv")),
        ("antimanchas",             ("antimanchas", "stain resistant", "no se mancha", "anti-manchas")),
        ("facil_limpieza",          ("facil de limpiar", "easy clean", "facil limpieza", "limpieza facil")),
        ("lavable",                 ("lavable", "washable", "se puede lavar")),
        ("preensamblado",           ("ya armado", "preensamblado", "pre assembled", "no armar", "viene armado")),
        ("sin_herramientas",        ("sin herramientas", "no tools", "sin destornillador", "tool free")),
        ("plug_and_play",           ("plug and play", "plug n play", "sin instalacion", "listo para usar", "out of the box")),
        ("gorilla_glass",           ("gorilla glass", "vidrio gorilla")),
        ("antireflejo",             ("antirreflejo", "anti reflejo", "anti glare", "sin reflejo")),
        ("brillo_alto",             ("brillo alto", "high brightness", "alto brillo", "muy brillante", "1000 nits")),
        # --- Smart Home avanzado ----------------------------------------------
        ("cerradura_smart",         ("cerradura inteligente", "smart lock", "cerradura wifi", "cerradura digital")),
        ("videoportero",            ("videoportero", "video portero", "portero visual", "doorbell")),
        ("camara_seguridad",        ("camara de seguridad", "cctv", "camara vigilancia", "ip camera")),
        ("luz_smart",               ("luz inteligente", "smart light", "bombilla smart", "led smart")),
        ("termostato_smart",        ("termostato inteligente", "smart thermostat", "termostato wifi")),
        ("enchufe_smart",           ("enchufe inteligente", "smart plug", "tomacorriente smart")),
        ("alarma_smart",            ("alarma inteligente", "smart alarm", "sistema de alarma")),
        ("aspersor_smart",          ("aspersor inteligente", "riego inteligente", "smart sprinkler")),
        ("sensor_puerta",           ("sensor de puerta", "door sensor", "contacto magnetico")),
        ("sensor_fuga_agua",        ("sensor de fuga", "leak detector", "detector agua")),
        ("hub_smart_home",          ("hub smart", "smart hub", "centralita domotica", "hub zigbee")),
        # --- Mascotas ---------------------------------------------------------
        ("comedero_automatico",     ("comedero automatico", "auto feeder", "alimentador automatico")),
        ("fuente_agua_mascota",     ("fuente de agua", "bebedero automatico", "water fountain pet")),
        ("rascador",                ("rascador", "scratcher", "poste rascador")),
        ("transportadora_mascota",  ("transportadora", "pet carrier", "kennel")),
        ("collar_gps",              ("collar gps", "gps mascota", "pet tracker")),
        ("camara_mascota",          ("camara mascota", "pet camera", "monitor mascota")),
        ("juguete_interactivo",     ("juguete interactivo", "pet interactive toy")),
        ("tipo_perro",              ("para perros", "para perro", "canino")),
        ("tipo_gato",               ("para gatos", "para gato", "felino")),
        # --- Bebés extras -----------------------------------------------------
        ("cuna",                    ("cuna", "moises", "moisés", "crib")),
        ("cuna_convertible",        ("cuna convertible", "convertible crib", "cuna que crece")),
        ("cochecito",               ("cochecito", "carriola", "stroller", "coche bebe")),
        ("silla_auto",              ("silla auto", "silla de auto", "car seat", "asiento de auto")),
        ("andadera",                ("andadera", "andador", "walker bebe")),
        ("corral",                  ("corral", "playpen", "parque bebe")),
        ("biberon",                 ("biberon", "biberón", "bottle baby")),
        ("esterilizador",           ("esterilizador", "sterilizer")),
        ("calentador_biberon",      ("calentador de biberon", "bottle warmer", "calienta biberones")),
        ("extractor_leche",         ("extractor de leche", "breast pump", "saca leche")),
        ("monitor_bebe",            ("monitor de bebe", "baby monitor", "video monitor bebe")),
        ("cambiador",               ("cambiador", "changing table")),
        ("humidificador_bebe",      ("humidificador bebe", "baby humidifier")),
        ("termometro_bebe",         ("termometro bebe", "baby thermometer")),
        ("ajustable_etapas",        ("ajustable", "adjustable", "que crece con el bebe", "varias etapas")),
        # --- Camping / outdoor ------------------------------------------------
        ("carpa",                   ("carpa", "tienda", "tent")),
        ("mosquitero",              ("mosquitero", "mosquito net", "anti mosquito")),
        ("saco_dormir",             ("saco de dormir", "sleeping bag", "bolsa dormir")),
        ("colchon_inflable",        ("colchon inflable", "air mattress", "matalas inflable")),
        ("termo",                   ("termo", "thermos", "termo de agua")),
        ("hielera_portatil",        ("hielera", "cooler", "nevera portatil", "conservadora")),
        ("linterna_recargable",     ("linterna recargable", "rechargeable flashlight", "linterna led")),
        ("fogon_portatil",          ("fogon portatil", "portable stove", "anafe portatil")),
        ("repelente_uv",            ("repelente uv", "proteccion uv outdoor")),
        ("kit_supervivencia",       ("kit supervivencia", "survival kit")),
        ("bolsa_dormir_temp",       ("temperatura limite", "comfort temp", "saco invierno")),
        # --- Gym / deportes ---------------------------------------------------
        ("cinta_correr",            ("cinta de correr", "treadmill", "trotadora")),
        ("bici_estatica",           ("bicicleta estatica", "bike spinning", "stationary bike")),
        ("eliptica",                ("eliptica", "elliptical")),
        ("set_pesas",               ("set de pesas", "weight set", "mancuernas")),
        ("mat_yoga",                ("mat de yoga", "esterilla yoga", "tapete yoga")),
        ("balon_pilates",           ("balon de pilates", "pilates ball", "fitball")),
        ("bandas_resistencia",      ("bandas elasticas", "bandas resistencia", "resistance bands")),
        ("guantes_boxeo",           ("guantes boxeo", "boxing gloves")),
        ("saco_boxeo",              ("saco de boxeo", "punching bag")),
        ("balon_futbol",            ("balon de futbol", "soccer ball", "pelota futbol")),
        ("balon_basquet",           ("balon basquet", "basketball")),
        ("para_natacion",           ("natacion", "swimming", "para nadar", "piscina")),
        ("para_correr",             ("para correr", "running", "trote", "jogging")),
        ("para_ciclismo",           ("ciclismo", "cycling", "bici road")),
        ("monitor_calorias",        ("monitor calorias", "calorie tracker", "contador calorias")),
        # --- Foto / video pro -------------------------------------------------
        ("camara_dslr",             ("dslr", "reflex digital", "camara reflex")),
        ("camara_mirrorless",       ("mirrorless", "sin espejo", "evil camera")),
        ("camara_compacta",         ("compacta", "point and shoot", "camara compacta")),
        ("camara_accion",           ("camara de accion", "action cam", "gopro", "camara go")),
        ("sensor_full_frame",       ("full frame", "fullframe", "sensor 35mm")),
        ("sensor_aps_c",            ("aps-c", "apsc", "sensor aps")),
        ("lente_prime",             ("lente fijo", "lente prime", "fixed lens")),
        ("lente_zoom",              ("lente zoom", "zoom lens", "objetivo zoom")),
        ("gimbal",                  ("gimbal", "estabilizador gimbal")),
        ("tripode",                 ("tripode", "trípode", "tripod")),
        ("monopode",                ("monopode", "monopod", "selfie stick", "palo selfie")),
        ("flash_externo",           ("flash externo", "external flash", "speedlite")),
        ("microfono_externo",       ("microfono externo", "external mic", "shotgun mic")),
        ("ring_light",              ("ring light", "aro de luz", "luz circular")),
        ("luz_softbox",             ("softbox", "luz softbox")),
        ("vlog_friendly",           ("vlog", "vloggers", "para vlog", "creador contenido")),
        # --- Cleaning robots --------------------------------------------------
        ("robot_aspiradora",        ("robot aspirador", "robot aspiradora", "robot vacuum", "roomba")),
        ("mapeo_casa",              ("mapeo casa", "lidar mapping", "mapeo laser")),
        ("trapeado",                ("trapea", "mopa", "mop", "lava piso")),
        ("estacion_autovaciado",    ("auto vaciado", "auto empty", "estacion vacio")),
        ("succion_alta",            ("succion alta", "high suction", "alta potencia succion", "succion potente")),
        ("filtro_pm25",             ("pm 2.5", "pm2.5", "filtro pm25", "particulas finas")),
        # --- Climate / Air ----------------------------------------------------
        ("aire_acondicionado",      ("aire acondicionado", "air conditioner", "ac split", "climatizador")),
        ("calefactor",              ("calefactor", "heater", "estufa electrica")),
        ("ventilador",              ("ventilador", "fan", "abanico")),
        ("ventilador_pie",          ("ventilador de pie", "stand fan", "ventilador parante")),
        ("ventilador_techo",        ("ventilador de techo", "ceiling fan", "abanico techo")),
        ("ventilador_torre",        ("ventilador torre", "tower fan")),
        ("ventilador_mesa",         ("ventilador de mesa", "table fan")),
        ("calefactor_ceramico",     ("calefactor ceramico", "ceramic heater")),
        ("estufa_aceite",           ("estufa de aceite", "oil heater", "radiador aceite")),
        ("purificador_aire",        ("purificador aire", "air purifier")),
        ("humidificador",           ("humidificador", "humidifier")),
        ("deshumidificador",        ("deshumidificador", "dehumidifier")),
        ("ac_inverter",             ("inverter ac", "ac inverter", "split inverter")),
        # --- Iluminación ------------------------------------------------------
        ("dimmer",                  ("regulable", "dimmer", "atenuador")),
        ("luz_blanca",              ("luz blanca", "white light", "luz fria", "cool white")),
        ("luz_calida",              ("luz calida", "warm light", "amarilla")),
        ("luz_rgb",                 ("rgb", "luz colores", "multicolor", "color changing")),
        ("solar_outdoor",           ("solar outdoor", "luz solar exterior", "lampara solar")),
        ("led",                     ("led", "luz led")),
        ("led_strip",               ("tira led", "led strip", "tira de luces")),
        # --- Office / impresoras ----------------------------------------------
        ("impresora_laser",         ("impresora laser", "laser printer")),
        ("impresora_tinta",         ("impresora tinta", "inkjet")),
        ("tinta_continua",          ("tinta continua", "ecotank", "tanque de tinta", "ink tank")),
        ("duplex",                  ("duplex", "doble cara", "dos caras")),
        ("escaner",                 ("escaner", "scanner", "escanea")),
        ("fax",                     ("fax",)),
        ("copiadora",               ("copia", "copiadora", "fotocopia")),
        ("a3",                      ("a3", "tamaño a3", "papel a3")),
        ("oficio",                  ("oficio", "papel oficio", "legal")),
        ("color_impresion",         ("imprime color", "color printing", "impresora color")),
        ("bn_impresion",            ("blanco y negro", "monochrome", "b/n")),
        # --- Beauty pro -------------------------------------------------------
        ("alisadora",               ("alisadora", "plancha de pelo", "hair straightener")),
        ("rizadora",                ("rizadora", "curling iron", "ondulador")),
        ("secador_pelo",            ("secador de pelo", "hair dryer", "secador profesional")),
        ("depiladora",              ("depiladora", "epilator")),
        ("ipl",                     ("ipl", "luz pulsada", "depilacion luz pulsada")),
        ("afeitadora",              ("afeitadora", "shaver", "rasuradora")),
        ("recortadora_barba",       ("recortadora", "trimmer barba", "barbero")),
        ("cortadora_pelo",          ("cortadora de pelo", "clipper", "maquina cortar pelo")),
        ("wet_dry",                 ("wet dry", "humedo y seco", "uso en mojado")),
        ("tecnologia_iones",        ("iones", "ionic technology", "tecnologia ionica", "anti frizz")),
        ("ceramica_pelo",           ("ceramica", "ceramic plates", "placas ceramicas")),
        ("turmalina",               ("turmalina", "tourmaline")),
        ("titanio_pelo",            ("titanio", "titanium plates", "placas titanio")),
        # --- Hogar emocional / regalos ----------------------------------------
        ("para_regalo",             ("regalo", "para regalar", "ideal para regalo", "gift", "obsequio")),
        ("empaque_regalo",          ("empaque regalo", "gift wrap", "empaquetado regalo")),
        ("regalo_aniversario",      ("aniversario", "regalo aniversario", "anniversary gift")),
        ("regalo_navidad",          ("navidad", "regalo navidad", "christmas gift")),
        ("regalo_dia_madre",        ("dia de la madre", "regalo mama", "para mama")),
        ("regalo_dia_padre",        ("dia del padre", "regalo papa", "para papa")),
        ("regalo_cumple",           ("cumpleaños", "regalo cumple", "birthday gift")),
        ("premium",                 ("premium", "alta gama", "lujo", "luxury", "high end")),
        ("edicion_limitada",        ("edicion limitada", "limited edition", "exclusivo")),
        ("mas_vendido",             ("mas vendido", "best seller", "top seller")),
        ("nuevo_lanzamiento",       ("nuevo", "lanzamiento", "new release", "recien salido")),
        # --- Restricciones / dietas (alimentos / cuidado personal) -----------
        ("sin_azucar",              ("sin azucar", "sugar free", "0 azucar")),
        ("sin_gluten",              ("sin gluten", "gluten free", "celiaco")),
        ("vegano",                  ("vegano", "vegan", "100% vegetal")),
        ("vegetariano",             ("vegetariano", "vegetarian")),
        ("organico",                ("organico", "orgánico", "organic", "ecologico")),
        ("natural",                 ("natural", "100% natural", "all natural")),
        ("sin_parabenos",           ("sin parabenos", "paraben free")),
        ("sin_sulfatos",            ("sin sulfatos", "sulfate free")),
        ("cruelty_free",            ("cruelty free", "no testeado animales")),
        # --- Texturas / acabados ----------------------------------------------
        ("acabado_mate",            ("mate", "matte", "acabado mate")),
        ("acabado_brillante",       ("brillante", "glossy", "brillo")),
        ("acabado_satinado",        ("satinado", "satin")),
        ("acabado_espejado",        ("espejado", "mirror finish", "efecto espejo")),
        ("texturizado",             ("texturizado", "textured")),
        # --- Modos profesionales / pre-sets ----------------------------------
        ("modo_pro",                ("modo pro", "pro mode", "modo profesional", "manual mode")),
        ("modo_juego",              ("modo juego", "game mode", "gaming mode")),
        ("modo_pelicula",           ("modo pelicula", "movie mode", "cinema mode")),
        ("modo_deporte",            ("modo deporte", "sports mode", "modo futbol")),
        # --- Compatibilidad consolas / accesorios -----------------------------
        ("ps5_compatible",          ("ps5", "playstation 5", "compatible ps5")),
        ("ps4_compatible",          ("ps4", "playstation 4")),
        ("xbox_compatible",         ("xbox", "xbox series", "xbox one", "xbox compatible")),
        ("switch_compatible",       ("nintendo switch", "switch compatible", "compatible switch")),
        # --- Soporte / postventa ----------------------------------------------
        ("servicio_24_7",           ("servicio 24/7", "soporte 24 horas", "atencion 24/7")),
        ("repuestos_disponibles",   ("repuestos", "spare parts", "piezas de repuesto")),
        ("instalacion_incluida",    ("instalacion incluida", "instalacion gratis")),
        ("entrega_a_domicilio",     ("entrega a domicilio", "delivery", "envio domicilio")),
        ("retiro_tienda",           ("retiro en tienda", "pickup tienda", "click and collect")),
        # --- Modos especiales (electro) ---------------------------------------
        ("modo_invitado",           ("modo invitado", "guest mode")),
        ("memoria_programa",        ("memoria de programa", "program memory")),
        ("modo_lluvia",             ("modo lluvia", "rain mode", "anti lluvia")),
        ("modo_invierno",           ("modo invierno", "winter mode")),
        ("modo_verano",             ("modo verano", "summer mode")),
        # --- Hogar muebles ---------------------------------------------------
        ("con_ruedas",              ("con ruedas", "wheels", "ruedas incluidas")),
        ("con_cajones",             ("con cajones", "drawers", "cajonera")),
        ("con_espejo",              ("con espejo", "espejo incluido", "mirror")),
        ("reclinable",              ("reclinable", "recliner", "se reclina")),
        ("giratorio",               ("giratorio", "swivel", "rotatorio")),
        ("memory_foam_material",    ("memory foam", "espuma memoria", "viscoelastica")),
        ("soporte_lumbar",          ("soporte lumbar", "lumbar support", "soporte espalda")),
        ("apoya_brazos",            ("apoyabrazos", "armrest", "apoya brazos")),
        ("ergonomico_oficina",      ("ergonomic office", "silla ergonomica", "para horas de oficina")),
        # --- Herramientas -----------------------------------------------------
        ("taladro",                 ("taladro", "drill")),
        ("taladro_percutor",        ("percutor", "rotomartillo", "hammer drill")),
        ("taladro_inalambrico",     ("taladro inalambrico", "cordless drill", "taladro a bateria")),
        ("soldadora",               ("soldadora", "welder", "soldar")),
        ("amoladora",               ("amoladora", "angle grinder", "esmeril")),
        ("sierra_circular",         ("sierra circular", "circular saw")),
        ("sierra_caladora",         ("sierra caladora", "jigsaw")),
        ("lijadora",                ("lijadora", "sander")),
        ("compresor_aire",          ("compresor de aire", "air compressor")),
        ("hidrolavadora",           ("hidrolavadora", "pressure washer", "lavadora alta presion")),
        ("juego_destornilladores",  ("juego destornilladores", "screwdriver set")),
        ("multimetro",              ("multimetro", "multimeter", "tester electrico")),
        ("pistola_calor",           ("pistola de calor", "heat gun", "termopistola")),
        # --- Auto / vehiculos -------------------------------------------------
        ("para_auto",               ("para auto", "para carro", "automotriz", "para vehiculo")),
        ("scooter_electrico",       ("scooter electrico", "patinete electrico", "e-scooter")),
        ("hoverboard",              ("hoverboard", "patineta electrica")),
        ("cargador_auto",           ("cargador para auto", "car charger", "12v cigarrillera")),
        ("aspiradora_auto",         ("aspiradora auto", "car vacuum", "aspirador para carro")),
        ("dash_cam",                ("dash cam", "camara auto", "dashcam")),
        ("gps_auto",                ("gps auto", "navegador gps", "gps para vehiculo")),
        # --- Termoelectronica / temperatura ----------------------------------
        ("control_temperatura",     ("control de temperatura", "temperature control")),
        ("temperatura_ajustable",   ("temperatura ajustable", "adjustable temperature")),
        ("alta_temperatura",        ("alta temperatura", "high temp")),
        ("conservacion_calor",      ("conservacion de calor", "keep warm")),
        # --- Smartwatch / wearable funciones ---------------------------------
        ("notificaciones_smartwatch", ("notificaciones smartwatch", "smart notifications")),
        ("control_musica_reloj",    ("control musica reloj", "music control")),
        ("contestar_llamadas",      ("contesta llamadas", "phone calls", "llamadas reloj")),
        ("modos_deporte_multi",     ("multi sport", "varios deportes", "modos deportivos")),
        ("monitor_estres",          ("monitor de estres", "stress tracker")),
        ("monitor_sueno",           ("monitor de sueno", "sleep tracker", "monitor sueño")),
        ("alarma_inteligente",      ("alarma inteligente", "smart alarm")),
        # --- Compatibilidad / standards ---------------------------------------
        ("usb_30",                  ("usb 3.0", "usb-3", "usb superspeed")),
        ("usb_32",                  ("usb 3.2", "usb-3.2")),
        ("usb_4",                   ("usb 4", "usb-4", "usb 4.0")),
        ("pcie_4",                  ("pcie 4", "pcie 4.0", "pcie x16")),
        ("pcie_5",                  ("pcie 5", "pcie 5.0")),
        ("ddr4",                    ("ddr4", "memoria ddr4")),
        ("ddr5",                    ("ddr5", "memoria ddr5")),
        # --- Audio extra ------------------------------------------------------
        ("subwoofer",               ("subwoofer", "subwoofer incluido", "graves potentes")),
        ("home_theater",            ("home theater", "cine en casa", "5.1", "7.1")),
        ("calidad_estudio",         ("calidad de estudio", "studio quality", "monitoring")),
        ("microfono_estudio",       ("microfono de estudio", "studio mic", "condenser")),
        # --- Productividad office --------------------------------------------
        ("auriculares_oficina",     ("auriculares oficina", "office headset", "tele trabajo")),
        ("escritorio_de_pie",       ("escritorio de pie", "standing desk", "altura ajustable escritorio")),
        ("monitor_oficina",         ("monitor oficina", "monitor productividad")),
        # --- Familias específicas ---------------------------------------------
        ("familia_grande",          ("familia grande", "para 5+ personas", "uso intensivo familia")),
        ("uso_individual",          ("individual", "single user", "para una persona", "soltero")),
        ("uso_compartido",          ("uso compartido", "multi-user", "varios usuarios")),
        # --- Accesibilidad ----------------------------------------------------
        ("alta_visibilidad",        ("alta visibilidad", "high visibility", "para baja vision")),
        ("teclado_grande",          ("teclas grandes", "big keys", "teclado adulto mayor")),
        ("audio_alto_volumen",      ("alto volumen", "loud", "amplificado", "para sordera leve")),
        # ========================================================================
        # MEGA RONDA 4: aún más sinónimos y categorías de comprador real
        # ========================================================================
        # --- País de origen / fabricación ------------------------------------
        ("made_in_usa",             ("made in usa", "fabricado en eeuu", "hecho en usa", "estadounidense")),
        ("made_in_china",           ("made in china", "fabricado en china", "hecho en china", "chino")),
        ("made_in_korea",           ("made in korea", "fabricado en corea", "coreano")),
        ("made_in_japan",           ("made in japan", "fabricado en japon", "japones", "japonés")),
        ("made_in_germany",         ("made in germany", "fabricado en alemania", "aleman", "alemán")),
        ("made_in_italy",           ("made in italy", "fabricado en italia", "italiano")),
        ("made_in_brazil",          ("made in brazil", "fabricado en brasil", "brasileño")),
        ("made_in_bolivia",         ("made in bolivia", "fabricado en bolivia", "boliviano", "produccion nacional")),
        ("ensamblado_bolivia",      ("ensamblado en bolivia", "armado en bolivia")),
        ("calidad_alemana",         ("calidad alemana", "german engineering")),
        ("calidad_japonesa",        ("calidad japonesa", "japanese quality")),
        ("calidad_coreana",         ("calidad coreana", "korean quality")),
        # --- Frecuencia de uso ------------------------------------------------
        ("uso_diario",              ("uso diario", "todos los dias", "daily use", "uso frecuente")),
        ("uso_eventual",            ("uso eventual", "de vez en cuando", "ocasional", "fin de semana")),
        ("uso_intensivo",           ("uso intensivo", "heavy duty", "uso pesado", "trabajo pesado")),
        ("uso_profesional",         ("uso profesional", "professional use", "uso pro")),
        ("uso_comercial",           ("uso comercial", "para negocio", "para tienda")),
        ("uso_industrial",          ("uso industrial", "industrial grade", "tipo industrial")),
        ("uso_domestico",           ("uso domestico", "uso hogareño", "para la casa")),
        ("uso_emergencia",          ("para emergencia", "emergency use", "kit emergencia")),
        ("grado_militar",           ("grado militar", "military grade", "tipo militar", "mil-spec")),
        ("grado_medico",            ("grado medico", "medical grade", "uso medico", "uso hospitalario")),
        ("grado_gastronomico",      ("grado gastronomico", "food grade", "para alimentos", "apto alimentos")),
        # --- Lugar / contexto de uso -----------------------------------------
        ("para_playa",              ("para la playa", "playa", "beach")),
        ("para_montaña",             ("para la montaña", "para la montana", "alta montaña", "trekking")),
        ("para_nieve",              ("para la nieve", "esqui", "ski", "snowboard")),
        ("para_terraza",            ("para terraza", "para balcon", "balcony", "rooftop")),
        ("para_jardin",             ("para jardin", "garden", "patio")),
        ("para_piscina",            ("para piscina", "pool", "alberca")),
        ("para_fiesta",             ("para fiesta", "party", "reunion", "para reuniones")),
        ("para_camping",            ("para camping", "camping", "acampar")),
        ("para_oficina_uso",        ("para oficina", "office use", "para escritorio")),
        ("para_taller",             ("para taller", "workshop", "garage")),
        ("para_baño",               ("para baño", "para baño", "bathroom", "para ducha")),
        ("para_cocina",             ("para cocina", "para la cocina", "kitchen")),
        ("para_dormitorio",         ("para dormitorio", "para cuarto", "bedroom")),
        ("para_sala",               ("para sala", "para living", "living room")),
        ("para_comedor",            ("para comedor", "dining room")),
        ("para_balcon",             ("para balcon", "balcony")),
        ("para_garaje",             ("para garaje", "garage")),
        ("para_outdoor_general",    ("para exterior", "outdoor", "intemperie", "al aire libre")),
        ("para_indoor_general",     ("para interior", "indoor", "techado")),
        # --- Eventos / regalos especificos -----------------------------------
        ("regalo_boda",             ("regalo de boda", "wedding gift", "lista de bodas", "casamiento")),
        ("regalo_baby_shower",      ("regalo baby shower", "baby shower")),
        ("regalo_quince",           ("para quinceañera", "para 15 años", "quince años", "sweet 15")),
        ("regalo_graduacion",       ("regalo graduacion", "graduation gift")),
        ("regalo_amigo_invisible",  ("amigo invisible", "secret santa", "amigo secreto")),
        ("regalo_san_valentin",     ("san valentin", "valentines", "dia del amor")),
        ("para_pareja",             ("para mi pareja", "para mi novio", "para mi novia", "para esposo", "para esposa")),
        ("para_amigo",              ("para amigo", "para amiga", "regalo amigo")),
        ("para_hermano",            ("para hermano", "para hermana", "regalo hermano")),
        ("para_jefe",               ("para jefe", "para mi jefe", "regalo jefe")),
        ("para_profesor",           ("para profesor", "para maestro", "para profe", "regalo profe")),
        ("para_abuelo",             ("para abuelo", "para abuela", "para los abuelos")),
        ("para_hijo",               ("para mi hijo", "para mi hija", "regalo hijo")),
        ("para_compadre",           ("para compadre", "para comadre")),
        # --- Estilos / decoracion --------------------------------------------
        ("estilo_moderno",          ("moderno", "modern", "modernito", "contemporaneo")),
        ("estilo_clasico",          ("clasico", "classic", "clásico")),
        ("estilo_vintage",          ("vintage", "retro estilo")),
        ("estilo_minimalista",      ("minimalista", "minimal", "simple")),
        ("estilo_escandinavo",      ("escandinavo", "scandinavian", "nordic")),
        ("estilo_industrial",       ("estilo industrial", "industrial style")),
        ("estilo_rustico",          ("rustico", "rustic")),
        ("estilo_boho",             ("boho", "bohemio", "bohemian")),
        ("estilo_art_deco",         ("art deco", "art déco")),
        ("estilo_colonial",         ("colonial", "estilo colonial")),
        ("estilo_japones",          ("japandi", "estilo japones", "zen")),
        ("estilo_glam",             ("glam", "glamoroso", "elegante", "lujo")),
        ("decorativo",              ("decorativo", "decoracion", "deco", "ornamento")),
        ("estetico",                ("estetico", "bonito", "lindo", "atractivo", "que se vea bien")),
        ("combinable",              ("combinable", "combina", "que combine")),
        # --- Niveles de habilidad --------------------------------------------
        ("nivel_principiante",      ("para principiante", "beginner", "facil", "para empezar")),
        ("nivel_intermedio",        ("nivel intermedio", "intermediate")),
        ("nivel_avanzado",          ("nivel avanzado", "advanced")),
        ("nivel_experto",           ("nivel experto", "expert", "profesional", "pro")),
        ("user_friendly",           ("user friendly", "facil de usar", "intuitivo", "intuitive")),
        # --- Genero / quien lo usa --------------------------------------------
        ("para_hombre",             ("para hombre", "para varon", "men", "masculino")),
        ("para_mujer",              ("para mujer", "para dama", "women", "femenino")),
        ("unisex_uso",              ("unisex", "ambos generos", "neutro")),
        ("para_niño",               ("para niño", "para chico", "boy")),
        ("para_niña",               ("para niña", "para chica", "girl")),
        # --- Edades especificas ----------------------------------------------
        ("edad_recien_nacido",      ("0-6 meses", "recien nacido", "newborn")),
        ("edad_lactante",           ("6-12 meses", "lactante")),
        ("edad_caminando",          ("1-3 años", "toddler", "que ya camina")),
        ("edad_preescolar",         ("3-6 años", "preescolar", "preschool")),
        ("edad_escolar",            ("6-12 años", "edad escolar", "school age")),
        ("edad_adolescente",        ("adolescente", "teen", "teenager", "joven")),
        ("edad_adulto",             ("adulto", "adult", "para adultos", "+18")),
        # --- Climas / Estaciones ---------------------------------------------
        ("para_invierno",           ("invierno", "winter", "frio", "época fria")),
        ("para_verano",             ("verano", "summer", "época calida")),
        ("para_lluvia",             ("para lluvia", "rainy", "época lluviosa", "epoca de lluvias")),
        ("clima_calido",            ("clima calido", "tropical", "calor", "calido")),
        ("clima_frio",              ("clima frio", "altiplano", "fria", "alta puna")),
        ("clima_humedo",            ("clima humedo", "humedad alta", "humid")),
        ("clima_seco",              ("clima seco", "arid", "sequedad")),
        # --- Sensoriales -----------------------------------------------------
        ("fragancia_natural",       ("fragancia natural", "huele bien", "aromatico", "perfumado")),
        ("sin_olor",                ("sin olor", "no huele", "neutral", "odorless")),
        ("tacto_suave",             ("suave al tacto", "soft touch", "blando", "softness")),
        ("con_vibracion",           ("vibra", "vibration", "vibrating")),
        ("con_sonido",              ("hace sonido", "with sound", "sonoro")),
        ("led_iluminado",           ("con luz", "iluminado", "led incluido")),
        # --- Bienestar / Wellness --------------------------------------------
        ("relajante",               ("relajante", "relaxing", "para relajar")),
        ("anti_ansiedad",           ("anti ansiedad", "calma ansiedad", "anxiety relief")),
        ("para_meditacion",         ("para meditar", "meditation", "yoga zen")),
        ("mejora_postura",          ("mejora postura", "corrige postura", "posture corrector", "anti-jorobado")),
        ("antifatiga",              ("antifatiga", "anti-fatigue", "anti cansancio")),
        ("anti_dolor",              ("anti dolor", "alivia dolor", "pain relief")),
        ("anti_estres",             ("anti estres", "anti-stress", "para el estres")),
        ("aromaterapia_uso",        ("aceites esenciales", "aromaterapia uso")),
        # --- Cocina especializada --------------------------------------------
        ("panificadora",            ("panificadora", "para hacer pan", "bread maker")),
        ("maquina_pasta",           ("maquina de pasta", "pasta maker", "para hacer fideos")),
        ("maquina_helado",          ("maquina de helado", "ice cream maker", "para hacer helado")),
        ("maquina_yogurt",          ("yogurtera", "para hacer yogurt", "yogurt maker")),
        ("maquina_cafe",            ("cafetera", "coffee maker", "espresso machine", "para cafe")),
        ("cafetera_capsula",        ("cafetera capsulas", "nespresso", "dolce gusto", "keurig")),
        ("cafetera_espresso",       ("espresso", "expresso", "cafe expresso")),
        ("molino_cafe",             ("molino de cafe", "coffee grinder")),
        ("vacuum_sealer",           ("envasadora al vacio", "vacuum sealer", "selladora vacio")),
        ("deshidratador",           ("deshidratador", "food dehydrator", "deshidrata frutas")),
        ("conveccion",              ("conveccion", "horno conveccion", "convection oven")),
        ("microondas_grill",        ("microondas grill", "grill incorporado", "with grill")),
        ("olla_presion",            ("olla a presion", "pressure cooker", "olla rapida")),
        ("olla_electrica",          ("olla electrica", "electric pot", "instant pot")),
        ("wok",                     ("wok", "para wok")),
        ("freidora_honda",          ("freidora honda", "deep fryer", "freidora profunda")),
        ("parrilla_incorporada",    ("parrilla", "grill", "asador", "barbacoa")),
        ("plancha_grill",           ("plancha", "griddle", "plancha cocina")),
        ("vaporera",                ("vaporera", "steamer", "al vapor cocina")),
        ("licuadora_inmersion",     ("licuadora de inmersion", "immersion blender", "minipimer")),
        ("procesador_alimentos",    ("procesador de alimentos", "food processor")),
        ("batidora_mano",           ("batidora de mano", "hand mixer")),
        ("batidora_pedestal",       ("batidora de pedestal", "stand mixer", "kitchenaid")),
        ("exprimidor",              ("exprimidor", "juicer", "extractor de jugo")),
        # --- Comidas / Restricciones -----------------------------------------
        ("apto_diabetico",          ("apto diabetico", "diabetic friendly", "para diabeticos")),
        ("apto_celiaco",            ("apto celiaco", "gluten free", "celiaco")),
        ("apto_lactosa",            ("sin lactosa", "lactose free", "lactosa")),
        ("apto_keto",               ("keto", "ketogenic", "cetogenica")),
        ("apto_paleo",              ("paleo", "dieta paleo")),
        ("low_carb",                ("low carb", "bajo en carbohidratos")),
        # --- Sostenibilidad extra --------------------------------------------
        ("biodegradable",           ("biodegradable", "se descompone")),
        ("compostable",             ("compostable", "para compost")),
        ("cien_pct_reciclado",      ("100% reciclado", "totalmente reciclado")),
        ("fair_trade",              ("fair trade", "comercio justo")),
        ("sin_plastico",            ("sin plastico", "plastic free", "cero plastico")),
        ("carbono_neutral",         ("carbono neutral", "carbon neutral", "huella cero")),
        ("plant_based",             ("plant based", "100% vegetal")),
        # --- Voltaje / electricidad -------------------------------------------
        ("voltaje_110",             ("110v", "110 voltios", "tipo americano")),
        ("voltaje_220",             ("220v", "220 voltios", "tipo europeo")),
        ("doble_voltaje",           ("doble voltaje", "110-220", "dual voltage")),
        # --- Iluminación específica ------------------------------------------
        ("lampara_escritorio",      ("lampara de escritorio", "desk lamp", "para escritorio")),
        ("lampara_mesa",            ("lampara de mesa", "table lamp")),
        ("lampara_pie",             ("lampara de pie", "floor lamp")),
        ("lampara_pared",           ("lampara de pared", "wall lamp", "aplique pared")),
        ("plafon",                  ("plafon", "plafonia", "ceiling lamp")),
        ("araña_luz",               ("araña", "candelabro", "chandelier")),
        ("luz_decorativa",          ("luz decorativa", "decorative light", "deco light")),
        # --- Profesiones especificas -----------------------------------------
        ("para_electricista",       ("para electricista", "electrician")),
        ("para_plomero",            ("para plomero", "plumber", "fontanero")),
        ("para_carpintero",         ("para carpintero", "carpenter")),
        ("para_mecanico",           ("para mecanico", "mechanic")),
        ("para_soldador",           ("para soldador", "welder pro")),
        ("para_panadero",           ("para panaderia", "baker")),
        ("para_pastelero",          ("para pasteleria", "pastry chef")),
        ("para_chef",               ("para chef", "chef profesional")),
        ("para_barista",            ("para barista", "barista pro")),
        ("para_barbero",            ("para barberia", "barber pro")),
        ("para_estilista",          ("para estilista", "para esteticista", "salon")),
        ("para_doctor",             ("para doctor", "para medico", "doctor use")),
        # --- Hobbies ---------------------------------------------------------
        ("para_tejido",             ("para tejer", "knitting", "tejido")),
        ("para_pintura",            ("para pintar", "para pintura", "painting")),
        ("para_dibujo",             ("para dibujar", "drawing", "ilustracion")),
        ("para_modelismo",          ("modelismo", "model making", "miniaturas")),
        ("para_rompecabezas",       ("rompecabezas", "puzzle", "armar puzzles")),
        ("para_lego",               ("lego", "para legos", "bloques")),
        ("para_coleccion",          ("coleccionable", "collectible", "para coleccionar")),
        ("para_jardineria",         ("jardineria", "gardening", "para plantas")),
        ("para_costura",            ("costura", "sewing", "para coser")),
        ("para_manualidades",       ("manualidades", "crafts", "diy crafts")),
        ("para_cerveza_casera",     ("cerveza casera", "homebrew", "hacer cerveza")),
        ("para_kombucha",           ("kombucha", "fermentacion bebida")),
        ("para_fermentacion",       ("fermentacion", "fermentation")),
        # --- Fiestas / Holidays -----------------------------------------------
        ("para_navidad",            ("navidad", "navideño", "christmas", "decoracion navidad")),
        ("para_halloween",          ("halloween", "disfraces halloween")),
        ("para_dia_muertos",        ("dia de los muertos", "todos santos", "todo santo")),
        ("para_carnaval",           ("carnaval", "carnival", "para carnaval", "para anata")),
        ("para_fiestas_patrias",    ("fiestas patrias", "patriotico", "6 de agosto")),
        ("para_pascua",             ("pascua", "easter", "pasqua")),
        ("para_san_juan",           ("san juan", "noche de san juan", "fogata")),
        # --- Música / Instrumentos --------------------------------------------
        ("para_guitarra",           ("para guitarra", "guitar")),
        ("para_piano",              ("para piano", "piano", "teclado musical")),
        ("para_bateria_musical",    ("bateria musical", "drums", "drum kit")),
        ("para_violin",             ("violin", "violín")),
        ("para_flauta",             ("flauta", "flute")),
        ("para_canto",              ("para canto", "para cantar", "vocal")),
        ("karaoke",                 ("karaoke", "para karaoke")),
        ("amplificador_musical",    ("amplificador", "amplifier", "amp musical")),
        # --- Casa eventos especiales ------------------------------------------
        ("para_mudanza",            ("para mudanza", "moving", "casa nueva")),
        ("para_alquiler",           ("para alquiler", "rental", "para alquilar")),
        ("para_airbnb",             ("para airbnb", "airbnb", "alquiler temporario")),
        ("para_hotel",              ("para hotel", "hotel grade", "uso hotelero")),
        ("para_oficina_uso2",       ("oficina corporativa", "office grade")),
        ("para_restaurante",        ("para restaurante", "restaurant", "uso gastronomico")),
        ("para_evento_grande",      ("para eventos", "evento grande", "catering")),
        # --- Tela / Material textil -------------------------------------------
        ("cien_pct_algodon",        ("100% algodon", "puro algodon", "all cotton")),
        ("lino_textil",             ("lino", "linen")),
        ("seda_textil",             ("seda", "silk")),
        ("lana_textil",             ("lana", "wool")),
        ("polar_textil",            ("polar", "fleece")),
        ("denim_textil",            ("denim", "mezclilla", "jean")),
        ("spandex_lycra",           ("spandex", "lycra", "elastico")),
        ("sintetico_textil",        ("sintetico", "polyester", "poliester")),
        ("nylon_textil",            ("nylon", "nailon")),
        # --- Tallas / medidas -------------------------------------------------
        ("talla_xs",                ("talla xs", "extra small", "muy pequeña")),
        ("talla_s",                 ("talla s", "small", "pequeña")),
        ("talla_m",                 ("talla m", "medium", "mediana")),
        ("talla_l",                 ("talla l", "large", "grande")),
        ("talla_xl",                ("talla xl", "extra large", "extra grande")),
        ("talla_xxl",               ("talla xxl", "doble extra grande")),
        ("talla_plus",              ("talla plus", "tallas grandes", "plus size", "para personas grandes")),
        ("talla_unica",             ("talla unica", "one size", "talla única")),
        ("talla_ajustable",         ("ajustable de talla", "size adjustable")),
        # --- Texturas tela / muebles ------------------------------------------
        ("acolchado",               ("acolchado", "padded", "almohadillado")),
        ("impermeable_tela",        ("tela impermeable", "waterproof fabric")),
        ("transpirable",            ("transpirable", "breathable", "respira")),
        ("anti_arrugas",            ("anti arrugas", "wrinkle free", "no se arruga")),
        # --- Limpieza profunda ------------------------------------------------
        ("autolavado_funcion",      ("auto lavado", "self wash")),
        ("antimicrobiano",          ("antimicrobiano", "antimicrobial", "anti germenes")),
        ("desinfectante",           ("desinfectante", "disinfectant", "sanitizante")),
        # --- Cocina / Bebidas extras ------------------------------------------
        ("dispensador_agua",        ("dispensador de agua", "water dispenser")),
        ("dispensador_hielo",       ("dispensador de hielo", "ice dispenser")),
        ("maquina_hielo",           ("maquina de hielo", "ice maker")),
        # --- Salud específica -------------------------------------------------
        ("monitor_oxigeno",         ("oximetro de pulso", "pulse oximeter", "satura cion")),
        ("balanza_inteligente",     ("balanza inteligente", "smart scale", "balanza digital")),
        ("nebulizador",             ("nebulizador", "nebulizer")),
        ("inhalador",               ("inhalador", "inhaler")),
        ("almohadilla_termica",     ("almohadilla termica", "heating pad")),
        ("ortopedico",              ("ortopedico", "orthopedic")),
        # --- Tipos de productos especifico ------------------------------------
        ("kit_completo",            ("kit completo", "viene con todo", "all included")),
        ("todo_en_uno",             ("todo en uno", "all in one", "all-in-one")),
        ("con_accesorios",          ("incluye accesorios", "with accessories", "viene con accesorios")),
        ("baterias_incluidas",      ("baterias incluidas", "batteries included", "con pilas")),
        ("sin_baterias",            ("sin baterias", "no batteries included")),
        ("cargador_incluido",       ("cargador incluido", "charger included")),
        ("estuche_incluido",        ("estuche incluido", "with case", "viene con estuche")),
        ("cable_incluido",          ("cable incluido", "cable included")),
        # --- Carácter del producto -------------------------------------------
        ("antiguo",                 ("antiguo", "old", "antique")),
        ("rebajado",                ("rebajado", "marked down", "saldo")),
        ("liquidacion",             ("liquidacion", "clearance", "remate")),
        ("oferta_relampago",        ("oferta relampago", "flash sale", "oferta del dia")),
        ("recomendado",             ("recomendado", "top pick", "recommended")),
        ("editores_pick",           ("editores pick", "editors choice")),
        ("tendencia",               ("tendencia", "trending", "lo mas pedido")),
        # --- Bebés extras MAS especifico --------------------------------------
        ("para_gemelos",            ("para gemelos", "doble bebe", "twin", "mellizos")),
        ("moises_portatil",         ("moises portatil", "portable bassinet")),
        ("monitor_sueno_bebe",      ("monitor sueño bebe", "baby sleep monitor")),
        ("cubre_lluvia_bebe",       ("cubre lluvia bebe", "rain cover stroller")),
        ("sombrilla_bebe",          ("sombrilla bebe", "stroller umbrella")),
        ("organizador_bebe",        ("organizador bebe", "baby organizer")),
        # --- Specific Office / Productivity -----------------------------------
        ("alfombrilla_mouse",       ("alfombrilla mouse", "mousepad", "mouse mat")),
        ("apoya_muñeca",            ("apoya muñeca", "wrist rest")),
        ("organizador_cables",      ("organizador cables", "cable management", "cable organizer")),
        ("regleta",                 ("regleta", "power strip", "multitoma")),
        ("ups",                     ("ups", "respaldo de energia", "no break", "battery backup")),
        ("estabilizador_voltaje",   ("estabilizador de voltaje", "voltage regulator", "anti-picos")),
        # --- Cocina utensilios específicos ------------------------------------
        ("set_cuchillos",           ("set de cuchillos", "knife set", "juego cuchillos")),
        ("juego_ollas",             ("juego de ollas", "cookware set", "set de cocina")),
        ("vajilla_completa",        ("vajilla completa", "dinnerware set", "juego vajilla")),
        ("set_cubiertos",           ("set de cubiertos", "cutlery set", "juego cubiertos")),
        ("organizador_cocina",      ("organizador cocina", "kitchen organizer")),
        ("tabla_picar",             ("tabla de picar", "cutting board")),
        # --- Hogar limpieza ---------------------------------------------------
        ("escoba_electrica",        ("escoba electrica", "stick vacuum", "aspirador escoba")),
        ("aspiradora_mano",         ("aspiradora de mano", "handheld vacuum", "aspiradora portatil")),
        ("aspiradora_central",      ("aspiradora central", "central vacuum")),
        ("limpiavidrios",           ("limpiavidrios", "robot limpiavidrios", "window cleaner")),
        ("trapeador_giratorio",     ("trapeador giratorio", "spin mop")),
        # --- Mascotas extras --------------------------------------------------
        ("ropa_mascota",            ("ropa para mascota", "ropa perro", "ropa gato")),
        ("juguete_mascota",         ("juguete mascota", "pet toy")),
        ("areneros_gatos",          ("arenero gato", "litter box", "arena gato")),
        ("cama_mascota",            ("cama mascota", "pet bed", "cama perro", "cama gato")),
        ("plato_mascota",           ("plato mascota", "pet bowl", "comedero")),
        ("rascador_techo",          ("rascador techo", "cat tree", "torre gato")),
        # --- Muebles / Almacenaje ---------------------------------------------
        ("estante",                 ("estante", "shelf", "estanteria", "repisa")),
        ("organizador_armario",     ("organizador armario", "closet organizer")),
        ("zapatero",                ("zapatero", "shoe rack", "estante zapatos")),
        ("perchero",                ("perchero", "coat rack")),
        ("escritorio",              ("escritorio", "desk")),
        ("silla_escritorio",        ("silla de escritorio", "desk chair", "office chair")),
        ("silla_gaming",            ("silla gaming", "gaming chair")),
        ("silla_comedor",           ("silla comedor", "dining chair")),
        ("mesa_centro",             ("mesa de centro", "coffee table", "mesa sala")),
        ("mesa_comedor",            ("mesa comedor", "dining table")),
        ("mesa_consola",            ("mesa consola", "console table")),
        ("sofa",                    ("sofa", "sillon", "couch")),
        ("sofa_cama",               ("sofa cama", "sleeper sofa", "futon")),
        ("colchon",                 ("colchon", "mattress")),
        ("cama_individual",         ("cama individual", "single bed", "1 plaza")),
        ("cama_matrimonial",        ("cama matrimonial", "queen bed", "2 plazas", "plaza y media")),
        ("cama_king",               ("cama king", "king size", "king bed")),
        ("cabecera_cama",           ("cabecera de cama", "headboard")),
        # --- Iluminación ambiental --------------------------------------------
        ("velas_aromaticas",        ("velas aromaticas", "scented candles", "velas perfumadas")),
        ("difusor_aroma",           ("difusor de aroma", "aroma diffuser")),
        # --- Belleza extras ---------------------------------------------------
        ("manicura_pedicura",       ("manicura", "pedicura", "manicure", "pedicure")),
        ("set_uñas",                ("set de uñas", "nail set", "kit manicura")),
        ("limpiador_facial",        ("limpiador facial", "face cleanser", "limpieza facial")),
        ("masajeador_facial",       ("masajeador facial", "face roller", "rodillo facial")),
        # --- Hogar / Aire libre extras ----------------------------------------
        ("piscina_inflable",        ("piscina inflable", "inflatable pool")),
        ("trampolin",               ("trampolin", "trampoline")),
        ("hamaca",                  ("hamaca", "hammock")),
        ("parasol",                 ("parasol", "umbrella patio", "sombrilla jardin")),
        ("set_jardin",              ("set jardin", "garden set")),
        ("muebles_jardin",          ("muebles jardin", "outdoor furniture")),
        # --- Energía solar / sostenibilidad -----------------------------------
        ("panel_solar",             ("panel solar", "solar panel")),
        ("bateria_litio",           ("bateria litio", "lithium battery", "litio")),
        ("powerbank",               ("power bank", "powerbank", "cargador portatil", "bateria externa")),
        # --- Identificación de mas detalles -----------------------------------
        ("certificado_ce",          ("certificado ce", "ce certified", "marca ce")),
        ("certificado_fcc",         ("fcc", "fcc certified")),
        ("certificado_rohs",        ("rohs", "rohs certified")),
        ("certificado_fda",         ("fda", "fda approved")),
        ("certificado_invima",      ("invima", "invima registrado")),
    )

    @classmethod
    def _cumple_atributos_json(cls, p, filtros: dict) -> bool:
        """Para los filtros boolean basados en atributos_texto / caracteristicas /
        descripción. Si el cliente exige el atributo, debe aparecer alguna de las
        palabras clave en el texto plano del producto. NULL-safe: si no hay
        ningún campo de texto, el producto no pasa cuando se exige el atributo."""
        haystack = cls._haystack_textual(p)
        if not haystack:
            for campo, _ in cls._ATRIBUTOS_BOOLEANOS:
                if filtros.get(campo):
                    return False
            return True
        for campo, keywords in cls._ATRIBUTOS_BOOLEANOS:
            esperado = filtros.get(campo)
            if not esperado:
                continue
            if not any(kw in haystack for kw in keywords):
                return False
        return True

    @staticmethod
    def _haystack_textual(p) -> str:
        """Concatenación lowercase de campos de texto del producto donde podemos
        buscar los atributos JSON declarados en la ficha."""
        partes = []
        for campo in ("atributos", "caracteristicas", "descripcion_extendida", "descripcion", "nombre"):
            val = getattr(p, campo, None)
            if val is None:
                continue
            if isinstance(val, dict):
                # atributos JSON dict {"Inverter": "Sí", ...}
                for k, v in val.items():
                    partes.append(f"{k}: {v}")
            else:
                partes.append(str(val))
        return " ".join(partes).lower()

    @staticmethod
    def _cumple_descuento(p, filtros: dict) -> bool:
        """Verifica que el producto tenga descuento real según el filtro:
        - tiene_descuento=True: debe haber precio_anterior > precio actual
        - descuento_pct_min: porcentaje de descuento >= valor pedido"""
        precio_anterior = getattr(p, "precio_anterior", None)
        precio_actual = float(p.precio.monto)
        anterior_monto = float(precio_anterior.monto) if precio_anterior is not None else None
        tiene_descuento = filtros.get("tiene_descuento")
        if tiene_descuento is True:
            if anterior_monto is None or anterior_monto <= precio_actual:
                return False
        descuento_min = filtros.get("descuento_pct_min")
        if descuento_min is not None:
            if anterior_monto is None or anterior_monto <= precio_actual:
                return False
            pct = (1 - precio_actual / anterior_monto) * 100
            if pct < descuento_min:
                return False
        return True

    @staticmethod
    def _cumple_stock_min(p, filtros: dict) -> bool:
        stock_min = filtros.get("stock_min")
        if stock_min is None:
            return True
        return getattr(p, "stock", 0) >= stock_min

    # --- Post Retrieval Validation ------------------------------------------

    _FILTROS_VERIFICABLES = (
        # (campo_filtro, atributo_producto, label_humano)
        ("precio_max", None, "precio"),
        ("precio_min", None, "precio mínimo"),
        ("ram_gb_min", "ram_gb", "RAM"),
        ("capacidad_gb_min", "capacidad_gb", "almacenamiento"),
        ("capacidad_litros_min", "capacidad_litros", "litros"),
        ("capacidad_kg_min", "capacidad_kg", "kg"),
        ("potencia_w_min", "potencia_w", "potencia"),
        ("pulgadas", "pulgadas", "tamaño"),
        ("pulgadas_min", "pulgadas", "tamaño mín"),
        ("tipo_panel", "tipo_panel", "panel"),
        ("resolucion", "resolucion", "resolución"),
        ("procesador", "procesador", "procesador"),
        ("refresh_hz_min", "refresh_hz", "Hz refresh"),
        ("gpu_dedicada", "gpu", "GPU dedicada"),
        ("bateria_mah_min", "bateria_mah", "batería mAh"),
        ("camara_mp_min", "camara_mp", "cámara MP"),
        ("camara_frontal_mp_min", "camara_frontal_mp", "cámara frontal MP"),
        ("soporta_5g", "soporta_5g", "5G"),
        ("sistema_operativo", "sistema_operativo", "sistema operativo"),
        ("meses_garantia_min", "meses_garantia", "garantía"),
        ("color", "color", "color"),
        ("marca", None, "marca"),
    )

    @classmethod
    def resumir_cumplimiento(cls, p, filtros: dict) -> str | None:
        """Retorna una línea de texto para el LLM cuando el resultado es escaso:
        'Cumple 4/6 filtros solicitados. Sin dato confirmado en ficha: GPU, Hz.'
        Devuelve None cuando no hay filtros activos o no hay nada relevante."""
        activos: list[str] = []
        faltantes: list[str] = []
        for campo, atributo, label in cls._FILTROS_VERIFICABLES:
            if not filtros.get(campo):
                continue
            activos.append(label)
            if atributo is None:
                continue
            val = getattr(p, atributo, None)
            if val is None:
                faltantes.append(label)
        if not activos:
            return None
        cumple = len(activos) - len(faltantes)
        total = len(activos)
        msg = f"Este resultado cumple {cumple}/{total} filtros solicitados."
        if faltantes:
            msg += f" Sin dato confirmado en ficha: {', '.join(faltantes)}."
        return msg

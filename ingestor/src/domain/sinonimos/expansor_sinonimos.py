from __future__ import annotations

import re


class ExpansorSinonimos:
    """Expande nombre_norm con variantes regionales/LATAM de los términos del producto.

    Dado un nombre_norm ya normalizado (sin acentos, minúsculas), busca cada
    clave del diccionario como palabra completa y agrega sus sinónimos si aún
    no están presentes. Así el índice FULLTEXT encuentra productos por cualquier
    variante regional sin depender de parches manuales en la BD.

    Algunas claves tienen contexto negativo (_EXCLUIR_SI): si alguna de esas
    palabras aparece en el nombre_norm, la expansión se omite para evitar
    falsos positivos (ej. 'refrigerador de cpu' no debe recibir 'heladera')."""

    _DICT: dict[str, list[str]] = {
        # ── BEBÉS ─────────────────────────────────────────────────────────────
        "bacinilla":     ["bacin", "orinal", "pelela", "vasenilla", "potty"],
        "basenilla":     ["bacin", "bacinilla", "orinal", "pelela", "vasenilla", "potty"],
        "potty":         ["bacin", "orinal", "pelela", "vasenilla", "bacinilla"],
        "orinal":        ["bacin", "pelela", "vasenilla", "bacinilla", "potty"],
        "coche":         ["carrito", "cochecito", "carriola", "silla paseo"],
        "biberon":       ["mamadera", "tetero"],
        "mamadera":      ["biberon", "tetero"],
        "cunita":        ["cuna", "moises"],
        "cuna":          ["cunita", "moises"],
        "chupete":       ["chupon", "tete"],
        "pañalera":      ["bolso maternal", "bolso bebe"],
        "portabebe":     ["canguro bebe", "mochila portabebe"],
        "andador":       ["walker bebe", "caminador bebe"],

        # ── REFRIGERACIÓN (excluir si contexto CPU/PC) ────────────────────────
        "refrigerador":  ["heladera", "nevera", "frigorifico", "refrigeradora"],
        "refrigeradora": ["heladera", "nevera", "frigorifico", "refrigerador"],
        "heladera":      ["refrigerador", "nevera", "frigorifico"],
        "nevera":        ["refrigerador", "heladera", "frigorifico"],
        "congelador":    ["freezer", "congeladora"],
        "congeladora":   ["freezer", "congelador"],
        "freezer":       ["congeladora", "congelador"],
        "conservadora":  ["cooler", "hielera", "nevera portatil"],
        "frigobar":      ["minibar", "nevera pequena"],

        # ── LAVADO ────────────────────────────────────────────────────────────
        "lavadora":      ["lavarropas", "lavarropa", "maquina lavar"],
        "lavasecadora":  ["lavadora secadora", "lavarropa secador"],
        "secadora":      ["secadora ropa", "secador ropa"],

        # ── COCINA LÍNEA BLANCA ───────────────────────────────────────────────
        "cocina":        ["fogon", "estufa cocina"],
        "encimera":      ["hornillas", "placa coccion", "quemadores"],
        "campana":       ["extractor cocina", "campana extractora"],
        "microondas":    ["horno microondas", "micro"],
        "horno":         ["horno electrico", "hornito"],

        # ── COCINA MENOR ──────────────────────────────────────────────────────
        "olla":          ["cacerola", "pote", "marmita"],
        "cacerola":      ["olla", "pote"],
        "sarten":        ["fridera", "paila"],
        "parrilla":      ["asador", "grill", "barbacoa", "barbecue"],
        "licuadora":     ["blender", "batidora de vaso"],
        "batidora":      ["mixer", "mezcladora"],
        "basurero":      ["papelera", "tacho basura", "bote basura", "caneca"],
        "termo":         ["botella termica", "termico"],
        "jarra":         ["pitcher", "cantaro"],
        "wok":           ["sarten china"],
        "tabla":         ["tabla picar", "tabla cortar"],
        "exprimidor":    ["juguera", "extractor jugos"],
        "picadora":      ["procesador alimentos", "procesadora"],

        # ── PEQUEÑOS ELECTRODOMÉSTICOS ────────────────────────────────────────
        "freidora":      ["air fryer", "freidora aire", "freidora sin aceite"],
        "sandwichera":   ["sandwichero", "tostador sandwich"],
        "waflera":       ["gofrera", "maquina waffles"],
        "tostadora":     ["tostador", "tostador pan"],
        "aspiradora":    ["aspirador", "vacuum"],
        "hidrolavadora": ["hidrolimpiadora", "lavadora presion", "karcher"],
        "arrocera":      ["olla arrocera", "cocedor arroz"],
        "cafetera":      ["maquina cafe", "cafetero"],
        "humidificador": ["vaporizador", "difusor", "nebulizador humedad"],

        # ── CLIMA ─────────────────────────────────────────────────────────────
        "ventilador":    ["abanico", "fan"],
        "calefon":       ["calentador agua", "boiler"],
        "termotanque":   ["tanque agua caliente", "boiler electrico"],
        "split":         ["aire acondicionado", "minisplit"],

        # ── CUIDADO PERSONAL ──────────────────────────────────────────────────
        "plancha":       ["planchita", "planchador", "iron"],
        "secador":       ["secadora pelo", "secador cabello", "hair dryer"],
        "alisadora":     ["plancha pelo", "planchita pelo", "alisador cabello",
                          "plancha cabello", "hair straightener"],
        "rizador":       ["ondulador", "tenaza rizar", "bucleador"],
        "afeitadora":    ["rasuradora", "maquina afeitar"],
        "perfume":       ["fragancia", "colonia", "eau de toilette", "edt"],
        "colonia":       ["perfume", "fragancia"],

        # ── SALUD ─────────────────────────────────────────────────────────────
        "oximetro":      ["pulsioximetro", "saturometro", "medidor oxigeno"],
        "tensiometro":   ["monitor presion", "baumanometro"],
        "nebulizador":   ["inhalador nebulizador"],
        "termometro":    ["medidor temperatura"],
        "bascula":       ["balanza", "pesa personal"],
        "glucometro":    ["medidor glucosa"],

        # ── TELEVISIÓN ────────────────────────────────────────────────────────
        "televisor":     ["tele", "television", "tv", "smart tv"],
        "television":    ["televisor", "tele", "tv"],

        # ── AUDIO ─────────────────────────────────────────────────────────────
        "parlante":      ["bocina", "altavoz", "speaker", "bafle"],
        "bocina":        ["parlante", "altavoz", "speaker"],
        "audifonos":     ["auriculares", "headphones", "earphones", "earbuds"],
        "auriculares":   ["audifonos", "headphones", "cascos"],
        "soundbar":      ["barra sonido"],

        # ── CELULARES / COMPUTACIÓN ───────────────────────────────────────────
        "celular":       ["telefono", "smartphone", "movil"],
        "smartphone":    ["celular", "telefono inteligente", "movil"],
        "laptop":        ["portatil", "computadora portatil", "notebook", "netbook"],
        "notebook":      ["laptop", "portatil", "computadora portatil"],
        "computadora":   ["computador", "pc", "ordenador"],
        "tablet":        ["tableta"],
        "impresora":     ["printer"],
        "pendrive":      ["usb", "memoria usb", "flash drive"],

        # ── DEPORTES / FITNESS ────────────────────────────────────────────────
        "bicicleta":     ["bici", "bike"],
        "caminadora":    ["trotadora", "cinta correr", "treadmill"],
        "eliptica":      ["eliptico", "maquina eliptica"],
        "mancuerna":     ["pesa mano", "dumbbell"],
        "colchoneta":    ["mat yoga", "yoga mat", "esterilla"],
        "mochila":       ["backpack", "bolso espalda"],
        "piscina":       ["alberca", "pileta", "pool inflable"],

        # ── MUEBLES ───────────────────────────────────────────────────────────
        "colchon":       ["mattress"],
        "sommier":       ["somier", "base cama"],
        "almohada":      ["almohadon"],
        "sofa":          ["sillon", "loveseat"],
        "escritorio":    ["desk", "mesa trabajo"],
        "ropero":        ["armario", "closet", "guardarropa"],
        "repisa":        ["estante", "anaquel"],
        "velador":       ["mesa noche", "mesita noche", "nochero"],

        # ── HOGAR / ILUMINACIÓN ───────────────────────────────────────────────
        "lampara":       ["luminaria", "farol"],
        "foco":          ["bombillo", "bombilla", "bulbo", "led"],
        "bombillo":      ["foco", "bombilla", "bulbo"],
        "trapeador":     ["mopa", "fregona"],

        # ── HERRAMIENTAS ──────────────────────────────────────────────────────
        "taladro":       ["perforadora", "drill"],
        "amoladora":     ["esmeril angular", "pulidora", "grinder"],
        "soldadora":     ["soldador", "maquina soldar"],

        # ── GAMING ────────────────────────────────────────────────────────────
        "consola":       ["videoconsola", "gaming console"],
        "joystick":      ["gamepad", "mando juego"],

        # ── ANIMALES / MASCOTAS ───────────────────────────────────────────────
        "pecera":        ["acuario"],
        "acuario":       ["pecera"],
        "mascotas":      ["animales domesticos", "pets"],
        "comedero":      ["plato mascota", "bowl mascota"],
        "bebedero":      ["dispensador agua mascota"],
        "transportadora":["jaula transporte", "caja transporte mascota"],
        "rascador":      ["arbol gato", "poste rascador"],

        # ── RELOJES ───────────────────────────────────────────────────────────
        "reloj":         ["watch", "cronografo", "timepiece"],
        "cronografo":    ["reloj", "cronometro", "watch"],
        "smartwatch":    ["reloj inteligente", "reloj smart", "wearable reloj"],
        "pulsera":       ["brazalete", "band", "correa"],

        # ── FOTOGRAFÍA ───────────────────────────────────────────────────────
        "camara":        ["camara fotos", "camara digital", "camara fotografica",
                          "camera"],
        "lente":         ["objetivo", "optica", "lens"],
        "tripode":       ["trípode", "soporte camara"],

        # ── JUGUETES ─────────────────────────────────────────────────────────
        "juguete":       ["toy", "juego nino", "juguetes ninos"],
        "muneca":        ["doll", "baby doll", "muñequita"],
        "peluche":       ["osito peluche", "stuffed animal", "peluches"],
        "rompecabezas":  ["puzzle", "puzle"],
        "lego":          ["bloques construccion", "armable", "bloques lego"],

        # ── REDES / CONECTIVIDAD ──────────────────────────────────────────────
        "router":        ["enrutador", "ruteador", "wifi router", "modem router"],
        "modem":         ["router modem", "gateway internet"],
        "repetidor":     ["extensor wifi", "amplificador wifi", "access point"],
        "antena":        ["antena wifi", "antena exterior"],

        # ── INSTRUMENTOS MUSICALES ────────────────────────────────────────────
        "guitarra":      ["instrumento cuerda", "guitar"],
        "piano":         ["teclado musical", "piano electrico", "keyboard musical"],
        "bateria":       ["drums", "kit bateria", "percusion"],
        "instrumento":   ["instrumento musical"],
        "microfono":     ["microfono condensador", "mic", "microphone"],
        "auricular":     ["audifonos", "headset"],

        # ── AUTOMOTRIZ / VEHÍCULOS ────────────────────────────────────────────
        "moto":          ["motocicleta", "scooter", "motociclo"],
        "motocicleta":   ["moto", "scooter", "moto electrica"],
        "scooter":       ["patineta electrica", "moto electrica", "moto scooter"],
        "bicicleta electrica": ["ebike", "e-bike", "bici electrica"],
        "carro":         ["auto", "automovil", "vehiculo"],
        "auto":          ["carro", "automovil", "vehiculo"],

        # ── HERRAMIENTAS JARDÍN ────────────────────────────────────────────────
        "podadora":      ["cortacesped", "podadoras", "cortadora pasto", "lawn mower"],
        "cortacesped":   ["podadora", "cortadora cesped"],
        "manguera":      ["manguera jardin", "manguera agua"],
        "regadera":      ["regadora", "watering can"],
        "bomba agua":    ["motobomba", "bomba presion agua"],

        # ── VIAJE / EQUIPAJE ──────────────────────────────────────────────────
        "maleta":        ["valija", "trolley", "equipaje", "maleta viaje"],
        "valija":        ["maleta", "trolley", "equipaje"],
        "maletin":       ["portafolio", "maletin trabajo"],

        # ── CAMPING / OUTDOOR ─────────────────────────────────────────────────
        "carpa":         ["tienda campaña", "tent", "camping tienda"],
        "saco dormir":   ["bolsa dormir", "sleeping bag"],
        "linterna":      ["torch", "flashlight", "linterna camping"],

        # ── SEGURIDAD / HOGAR ─────────────────────────────────────────────────
        "caja fuerte":   ["cofre seguridad", "safe box", "caja seguridad"],
        "cerradura":     ["cerrojo", "candado", "lock"],
        "alarma":        ["alarma casa", "sistema alarma", "sensor alarma"],
        "camara seguridad": ["camara vigilancia", "cctv", "ip cam", "camara ip"],

        # ── SMART HOME ────────────────────────────────────────────────────────
        "enchufe inteligente": ["smart plug", "toma corriente smart",
                                "enchufe wifi"],
        "bombilla inteligente": ["smart bulb", "foco inteligente", "led smart"],
        "asistente virtual": ["smart speaker", "bocina inteligente",
                              "altavoz inteligente"],

        # ── ORGANIZACIÓN / HOGAR ──────────────────────────────────────────────
        "organizador":   ["caja organizadora", "contenedor organizar",
                          "canasto organizer"],
        "estanteria":    ["estante", "repisa", "rack", "shelving"],
        "perchero":      ["colgador ropa", "rack ropa"],

        # ── HOME THEATER / AUDIO HOGAR ────────────────────────────────────────
        "home theater":  ["teatro en casa", "home cinema", "sistema cine casa"],
        "minicomponente":["equipo sonido", "equipo musica", "micro cadena"],
        "equipo sonido": ["minicomponente", "equipo musical", "micro cadena"],

        # ── CABLES / CONECTORES ────────────────────────────────────────────────
        "extension":     ["alargador", "alargue", "extension electrica",
                          "zapatilla electrica"],
        "cable hdmi":    ["hdmi cable", "cable 4k"],
        "cable usb":     ["usb cable", "cable datos", "cable carga"],

        # ── COCINA MENOR ADICIONAL ────────────────────────────────────────────
        "vaso":          ["copa", "cristaleria", "vasija"],
        "copa":          ["vaso", "cristaleria", "wine glass"],
        "molde":         ["molde reposteria", "bandeja hornear", "forma reposteria"],

        # ── PURIFICADORES ─────────────────────────────────────────────────────
        "purificador":   ["filtro agua", "purificador agua", "filtrador agua"],
        "osmosis":       ["purificador osmosis", "filtro osmosis"],

        # ── COSTURA ───────────────────────────────────────────────────────────
        "maquina de coser": ["costurera", "maquina costura", "sewing machine"],
        "overlock":      ["overlok", "remalladora", "maquina overlock"],
    }

    # Claves que NO se expanden si el nombre_norm también contiene alguna de estas palabras.
    # Evita falsos positivos como "refrigerador de cpu" → "heladera".
    _EXCLUIR_SI: dict[str, list[str]] = {
        # Refrigeración: no expandir si es cooler de PC
        "refrigerador":  ["cpu", "cooler", "procesador", "gaming"],
        "refrigeradora": ["cpu", "cooler", "procesador"],
        "heladera":      ["cpu", "cooler", "procesador"],
        "nevera":        ["cpu", "cooler", "procesador"],
        "congelador":    ["cpu", "cooler"],
        "congeladora":   ["cpu", "cooler"],
        "freezer":       ["cpu", "cooler"],
        # Batería: no agregar terms de batería de instrumentos si es batería de dispositivo
        "bateria":       ["celular", "telefono", "laptop", "portatil", "tablet",
                          "smartphone", "autonomia"],
        # Cámara: no agregar terms de fotografía si es cámara de seguridad
        "camara":        ["seguridad", "vigilancia", "cctv", "ip"],
        # Extensión: no expandir si es extensión de cabello/uñas
        "extension":     ["cabello", "pelo", "unas", "cabello"],
        # Carro: no expandir "carro de compras" como auto/vehículo
        "carro":         ["compras", "super", "supermercado"],
    }

    _PATTERNS: dict[str, re.Pattern] = {
        clave: re.compile(r"\b" + re.escape(clave) + r"\b")
        for clave in _DICT
    }

    @classmethod
    def expandir(cls, nombre_norm: str) -> str:
        """Añade sinónimos al nombre_norm. Devuelve el string extendido."""
        if not nombre_norm:
            return nombre_norm
        extras: set[str] = set()
        for clave, pattern in cls._PATTERNS.items():
            if not pattern.search(nombre_norm):
                continue
            exclusiones = cls._EXCLUIR_SI.get(clave, [])
            if any(ex in nombre_norm for ex in exclusiones):
                continue
            for sinonimo in cls._DICT[clave]:
                if sinonimo not in nombre_norm:
                    extras.add(sinonimo)
        if not extras:
            return nombre_norm
        return nombre_norm + " " + " ".join(sorted(extras))

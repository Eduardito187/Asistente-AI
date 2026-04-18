from __future__ import annotations

from typing import List, Tuple

from .regla_categoria import ReglaCategoria

SIN_CATEGORIA: Tuple[str, str] = ("General", "Otros")


# Orden importa: patrones mas especificos primero.
REGLAS: List[ReglaCategoria] = [
    ReglaCategoria("Televisores",       "Smart TV",         r"\b(smart\s*tv|televisor|televisi[oó]n|\btv\b|pantalla led|oled|qled)\b"),
    ReglaCategoria("Celulares",         "Smartphones",      r"\b(celular|smartphone|tel[ée]fono m[oó]vil|iphone|galaxy|redmi|xiaomi|huawei)\b"),
    ReglaCategoria("Laptops",           "Notebooks",        r"\b(laptop|notebook|portatil|port[aá]til|macbook|chromebook|ultrabook)\b"),
    ReglaCategoria("Computación",       "PC Escritorio",    r"\b(pc escritorio|desktop|computador(?:a)?|torre|all[-\s]?in[-\s]?one)\b"),
    ReglaCategoria("Computación",       "Monitores",        r"\b(monitor|pantalla pc|display\s*\d+)\b"),
    ReglaCategoria("Computación",       "Accesorios",       r"\b(teclado|mouse|mousepad|webcam|docking|hub usb|memoria (?:usb|ram)|disco (?:duro|ssd)|ssd|pendrive|cargador laptop)\b"),
    ReglaCategoria("Impresión",         "Impresoras",       r"\b(impresora|multifuncional|toner|t[oó]ner|cartucho|tinta\b)\b"),
    ReglaCategoria("Gaming",            "Consolas",         r"\b(playstation|\bps5\b|\bps4\b|xbox|nintendo switch|nintendo\b)\b"),
    ReglaCategoria("Gaming",            "Accesorios",       r"\b(joystick|gamepad|mando|control(?:ador)? ps\d|control xbox|volante gamer)\b"),
    ReglaCategoria("Audio",             "Parlantes",        r"\b(parlante|altavoz|bocina|soundbar|speaker|bluetooth speaker)\b"),
    ReglaCategoria("Audio",             "Audífonos",        r"\b(aud[íi]fonos?|auriculares?|headphones?|earbuds|in[-\s]?ear)\b"),
    ReglaCategoria("Audio",             "Home Theater",     r"\b(home theater|home cinema|equipo de sonido|minicomponente|microcomponente)\b"),
    ReglaCategoria("Refrigeración",     "Refrigeradores",   r"\b(refrigerador|heladera|nevera|frigobar|freezer|congelador)\b"),
    ReglaCategoria("Cocina",            "Cocinas",          r"\b(cocina (?:a gas|el[eé]ctrica|de \d)|anafe|hornalla|vitrocer[aá]mica)\b"),
    ReglaCategoria("Cocina",            "Hornos",           r"\b(horno|microondas|horno tostador)\b"),
    ReglaCategoria("Cocina",            "Campanas",         r"\b(campana extractora|extractor de cocina)\b"),
    ReglaCategoria("Lavado",            "Lavadoras",        r"\b(lavadora|lava[-\s]?secadora|secadora)\b"),
    ReglaCategoria("Lavado",            "Planchas",         r"\b(plancha a vapor|plancha el[eé]ctrica|planchado)\b"),
    ReglaCategoria("Climatización",     "Aires",            r"\b(aire acondicionado|split|climatizador)\b"),
    ReglaCategoria("Climatización",     "Ventilación",      r"\b(ventilador|calentador|calefactor|estufa (?:el[eé]ctrica|a gas)|purificador)\b"),
    ReglaCategoria("Pequeños Electrodomésticos", "Licuadoras", r"\b(licuadora|batidora|procesador de alimentos|extractor de jugos|juguera)\b"),
    ReglaCategoria("Pequeños Electrodomésticos", "Cafeteras", r"\b(cafetera|espresso|molinillo de caf[eé])\b"),
    ReglaCategoria("Pequeños Electrodomésticos", "Freidoras", r"\b(freidora|air\s*fryer)\b"),
    ReglaCategoria("Pequeños Electrodomésticos", "Ollas",    r"\b(olla arrocera|olla a presi[oó]n|olla el[eé]ctrica|multi[-\s]?olla|sart[eé]n el[eé]ctrica)\b"),
    ReglaCategoria("Pequeños Electrodomésticos", "Hervidores", r"\b(hervidor|tetera el[eé]ctrica)\b"),
    ReglaCategoria("Pequeños Electrodomésticos", "Aspiradoras", r"\b(aspiradora|robot aspirador)\b"),
    ReglaCategoria("Cuidado Personal",  "Afeitadoras",      r"\b(afeitadora|rasuradora|recortador(?:a)?|trimmer)\b"),
    ReglaCategoria("Cuidado Personal",  "Secadores",        r"\b(secador(?:a)? de (?:pelo|cabello)|plancha de pelo|rizador)\b"),
    ReglaCategoria("Cuidado Personal",  "Cuidado Bucal",    r"\b(cepillo dental el[eé]ctrico|irrigador|waterpik)\b"),
    ReglaCategoria("Salud",             "Cuidado Salud",    r"\b(ox[ií]metro|term[oó]metro|tensi[oó]metro|glucometro|nebulizador|masajeador)\b"),
    ReglaCategoria("Bebés",             "Bebés",            r"\b(beb[eé]|infantil|cuna|cochecito|pa[ñn]al|biber[oó]n|silla de auto)\b"),
    ReglaCategoria("Juguetería",        "Juguetes",         r"\b(juguete|mu[ñn]eca|peluche|lego|bloques|\bjuego didactico\b|juego didáctico)\b"),
    ReglaCategoria("Deportes",          "Fitness",          r"\b(bicicleta|caminadora|trotadora|el[íi]ptica|mancuerna|pesa|yoga mat|colchoneta)\b"),
    ReglaCategoria("Deportes",          "Outdoor",          r"\b(camping|bolsa de dormir|carpa|mochila de trekking|casco)\b"),
    ReglaCategoria("Muebles",           "Muebles",          r"\b(silla|sof[aá]|mesa|escritorio|mueble|estanter[íi]a|repisa|colch[oó]n|cama |ropero)\b"),
    ReglaCategoria("Hogar",             "Iluminación",      r"\b(l[aá]mpara|foco\b|luminaria|araña|plafon|bombillo)\b"),
    ReglaCategoria("Hogar",             "Decoración",       r"\b(cortina|alfombra|cuadro|espejo|flore(?:ro|s) artificial|organizador)\b"),
    ReglaCategoria("Hogar",             "Cocina Menor",     r"\b(sart[eé]n|olla(?!\s*el[eé]ctrica)|taza|plato|vaso|cuchillo|cuber)"),
    ReglaCategoria("Hogar",             "Limpieza",         r"\b(escoba|trapeador|detergente|desinfectante|lavandina|limpiador)\b"),
]

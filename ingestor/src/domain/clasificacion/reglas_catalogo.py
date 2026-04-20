from __future__ import annotations

from typing import List, Tuple

from .regla_categoria import ReglaCategoria

SIN_CATEGORIA: Tuple[str, str] = ("General", "Otros")

_CAT_ACC_TV = "Accesorios TV"
_CAT_CLIMA = "Climatización"
_CAT_COMPU = "Computación"
_CAT_PEQ = "Pequeños Electrodomésticos"
_CAT_CPER = "Cuidado Personal"
_CAT_HOGAR = "Hogar"
_CAT_BEBES = "Bebés"
_CAT_JUGUE = "Juguetería"
_CAT_AUDIO = "Audio"
_CAT_MUEBLES = "Muebles"
_CAT_RELOJ = "Relojería"
_CAT_SEG = "Seguridad"


_CAT_REFRI = "Refrigeración"
_CAT_LAVADO = "Lavado"
_CAT_COCINA = "Cocina"
_CAT_TV = "Televisores"
_CAT_LAP = "Laptops"
_CAT_IMPR = "Impresión"
_CAT_GAMING = "Gaming"
_CAT_CEL = "Celulares"
_CAT_TAB = "Tablets"
_CAT_SW = "Smartwatch"
_CAT_FOTO = "Fotografía"
_CAT_SALUD = "Salud"
_CAT_DEP = "Deportes"
_CAT_COC_MEN = "Cocina Menor"
_CAT_HERR = "Herramientas"
_CAT_AUTO = "Automotriz"
_CAT_MASC = "Mascotas"


# Orden importa: patrones mas especificos primero. Reglas se aplican SOLO
# sobre el nombre del producto para evitar falsos positivos por descripciones
# largas (p.ej. un soporte cuya descripcion menciona "televisor" 10 veces).
REGLAS: List[ReglaCategoria] = [
    # --- Accesorios primero (evitan que contaminen categorias reales) ---
    ReglaCategoria(_CAT_ACC_TV,  "Soportes",         r"\bsoporte (?:de pared |para |tv |universal ).*(?:tv|\d+\")\b|\bsoporte\s+(?:tv|universal|de\s+tv)\b|\brack\s+tv\b|\bsoporte\s+de\s+tv\b|\bmontaje\s+de\s+barra\s+de\s+sonido\b"),
    ReglaCategoria(_CAT_ACC_TV,  "TV Stick",         r"\btv\s*stick\b|\bchromecast\b|\bfire\s*stick\b|\btv\s*box\b|\bandroid\s+tv\s+box\b|\bmaster[-\s]?g\b"),
    ReglaCategoria(_CAT_ACC_TV,  "Control Remoto",   r"\bcontrol remoto (?:universal|tv)\b"),
    ReglaCategoria(_CAT_ACC_TV,  "Proyectores",      r"\bproyector\b"),

    # --- Electrodomesticos mayores (priorizan sobre "Hogar" generico) ---
    ReglaCategoria(_CAT_REFRI,   "Refrigeradores",   r"\b(refrigerador(?:a)?|heladera|nevera|frigobar|freezer|congelador|side by side|visi\s*cooler|exhibidor\s+vertical|vinera|cava\s+(?:de\s+vinos?|\d+\s*l\b)|vitrina\s+(?:mantenedor|refrigerad)\w*|auto\s+servicio\s+(?:vanguard\s+)?refrigerad\w*|expositor\s+(?:de\s+carnes|refrigerad\w*))\b"),
    ReglaCategoria(_CAT_LAVADO,  "Lavadoras",        r"\b(lavadora|lava[-\s]?secadora|secadora)\b"),
    ReglaCategoria(_CAT_COCINA,  "Cocinas",          r"\b(cocina(?: a gas| el[eé]ctrica| de \d)?|anafe|hornalla|vitrocer[aá]mica|encimera|freidor\s+a\s+gas|m[aá]quina\s+expendedora|placa\s+de\s+gas)\b"),
    ReglaCategoria(_CAT_COCINA,  "Microondas",       r"\b(microondas|horno microondas)\b"),
    ReglaCategoria(_CAT_COCINA,  "Hornos",           r"\b(horno(?: el[eé]ctrico| tostador)?)\b"),
    ReglaCategoria(_CAT_COCINA,  "Campanas",         r"\b(campana(?: extractora| de isla| decorativa)?|extractor de cocina|extractor\s+(?:bloom|dualis|cx\d)|filtro\s+de\s+carbon\s+activo)\b"),
    ReglaCategoria(_CAT_CLIMA,   "Aire Acondicionado", r"\b(aire acondicionado|aa split|split inverter|minisplit)\b"),
    ReglaCategoria(_CAT_CLIMA,   "Ventiladores",     r"\b(ventilador|climatizador|purificador(?:es)?\s+(?:de\s+aire|3\s+en\s*1|slim|\d+cm)|purificador\b|extractor (?:para pared|de ba[ñn]o))\b"),
    ReglaCategoria(_CAT_CLIMA,   "Calefones",        r"\b(calef[oó]n|termo\s*tanques?|termontanques?|tt\s+rheem|calentador(?:es)? de agua)\b"),

    # --- Computacion / Gaming / Telefonia ---
    ReglaCategoria(_CAT_TV,      "Smart TV",         r"^televisor\b|\b(televisor|tv\s+\d+\"?|smart tv)\b"),
    ReglaCategoria(_CAT_LAP,     "Notebooks",        r"\b(notebook|laptop|macbook|chromebook|ultrabook|portatil|ideapad(?:\s+slim)?|thinkpad|pavilion|vivobook|zenbook)\b"),
    ReglaCategoria(_CAT_COMPU,   "PC Escritorio",    r"\b(pc escritorio|desktop|computadoras?\s+(?:de\s+(?:escritorio|mesa)|todo\s+en\s+uno|apple|mac)|torre gamer|all[-\s]?in[-\s]?one|todo\s+en\s+uno|mini[-\s]?pc)\b"),
    ReglaCategoria(_CAT_COMPU,   "Oficina",          r"\b(cajas?\s+registradoras?|esc[aá]ner\s+(?:de\s+)?c[oó]digo\s+(?:de\s+)?barras?|lector\s+(?:de\s+)?c[oó]digo\s+(?:de\s+)?barras?|contadoras?\s+(?:comercial|de\s+billetes)|ribbon\s+(?:cera|de\s+cera)|tarjetas?\s+(?:\w+\s+)?(?:micro\s*sd|sd\s+)?\d+\s*gb|tarjeta\s+\w*\s*microsd|micro\s*sdxc|\bsdxc\b)\b"),
    ReglaCategoria(_CAT_COMPU,   "Monitores",        r"\b(monitor\b|pantalla pc)\b"),
    ReglaCategoria(_CAT_COMPU,   "Energía",          r"\b(fuente de poder|power bank|bancos?\s+de\s+energ[ií]a|\bups\b|ups\s+(?:interactivo|online)|regulador de voltaje|estabilizador|ups\s+\d|regletas?|supresor(?:es)?\s+(?:de\s+picos?|de\s+voltaje)|cargador\s+magn[eé]tico|charge\s+['n][\w ]*go)\b"),
    ReglaCategoria(_CAT_COMPU,   "Redes",            r"\b(routers?|access point|\bap\s+wifi|switch\s+(?:\d+\s*puertos?|ds-|gigabit|\d+\s*gb)|switch\b|modem|repetidor (?:de )?wifi|extensor wifi|sistemas?\s+(?:wi[-\s]?fi\s+)?mesh|deco\s+(?:pack|e\d|m\d)|sistema\s+inal[aá]mbrico|starlink(?:\s+mini)?|kit\s+starlink)\b"),
    ReglaCategoria(_CAT_COMPU,   "Accesorios",       r"\b(teclado|mouse|mousepad|webcam|c[aá]mara\s+web|docking|hub usb|memoria (?:usb|ram)|disco (?:duro|ssd)|\bssd\b|pendrive|cargador laptop|adaptador (?:hub|tipo c)|cable hdmi|gabinete (?:gamer|pc)|enchufe (?:inteligente|wifi|smart)|cargadores?\s+(?:magn|usb|tipo|uno|gan|nexode|r[aá]pido|inal[aá]mbrico|para\s+iphone|magsafe)|magsafe|airtag|atenuador\s+(?:de\s+luz|inteligente)|calculadoras?(?:\s+(?:gr[aá]fica|cient[ií]fica|graficadora|casio|escolar|resistente|de\s+verificaci|programable|wd[-\s]?\d|fx[-\s]?\d))?|lector\s+de\s+c[oó]digo|mac\s+mini|computadora\s+(?:apple|mac)|contadoras?\s+comercial(?:es)?|flash\s+memory|flash\s+usb\b)\b"),
    ReglaCategoria(_CAT_IMPR,    "Impresoras",       r"\b(impresora|multifuncional|t[oó]ner|cartucho (?:de tinta)?|tinta (?:original|recargable)|botella\s+de\s+tinta|refil\s+(?:universal|de\s+tinta))\b"),
    ReglaCategoria(_CAT_GAMING,  "Consolas",         r"\b(playstation|\bps\s*[34-5]\b|xbox|nintendo switch|nintendo\b)\b"),
    ReglaCategoria(_CAT_GAMING,  "Accesorios",       r"\b(joystick|gamepad|control ps\d|control xbox|volante gamer|dualsense|dualshock|case\s+gaming|gabinete\s+gamer|auriculares?\s+(?:para\s+juegos?|gaming)|auricular\s+(?:para\s+)?juegos?|mando\s+(?:inal[aá]mbrico\s+)?(?:logitech|razer|gamer)|lector\s+de\s+disco\s+externos?\s+(?:para\s+)?(?:ps|playtation|playstation))\b"),
    ReglaCategoria(_CAT_GAMING,  "VR",               r"\b(gafas\s+(?:de\s+)?realidad\s+virtual|meta\s+quest|oculus(?:\s+quest)?|headset\s+vr|vr\s+headset)\b"),
    # Smartwatch antes que Smartphones: "correa para galaxy watch7" no debe
    # caer en celulares.
    ReglaCategoria(_CAT_SW,      "Smartwatch",       r"\b(smartwatch|smart watch|apple\s*watch|applewatch|reloj inteligente|galaxy\s+watch\d*|mi band|mi watch)\b"),
    ReglaCategoria(_CAT_SW,      "Accesorios",       r"\bcorrea\s+(?:deportiva\s+)?(?:\([^)]*\)\s+)?para\s+galaxy\s+watch|\bbanda\s+para\s+(?:apple\s*watch|galaxy\s+watch)"),
    # Accesorios de celular ANTES de Smartphones: "estuche para celular",
    # "portarollo con soporte para telefono", "microfono con entrada iphone",
    # "soporte vehicular para celular", "bolson porta celular" — nada de eso
    # es un smartphone.
    ReglaCategoria(_CAT_CEL,     "Accesorios",       r"\b(fundas?(?:\s+\w+){0,3}\s+(?:de\s+silicona|con\s+magneto|para\s+(?:celular|iphone|galaxy|tel[eé]fono))|estuches?(?:\s+\w+){0,3}\s+(?:para|de)\s+(?:celular|iphone|galaxy|tel[eé]fono)|protectores?\s+de\s+pantalla|vidrios?\s+templados?|cables?\s+lightning|bols[oó]n\s+porta\s+(?:celular|tel[eé]fono)|porta\s*rollos?(?:\s+\w+){0,5}\s+para\s+(?:tel[eé]fono|celular)|soportes?\s+(?:vehicular(?:es)?|universal(?:es)?|magn[eé]tico|de\s+auto|para)(?:\s+\w+){0,4}\s+(?:para\s+)?(?:celular|tel[eé]fono|iphone|galaxy)|cargadores?\s+(?:magn[eé]tico\s+)?para\s+(?:iphone|celular|galaxy))\b"),
    # Tablets antes que Smartphones: "tablet xiaomi redmi pad" no debe
    # terminar en Smartphones.
    ReglaCategoria(_CAT_TAB,     "Tablets",          r"\btablet\b|\bipad\b|\bxiaomi\s+(?:pad|redmi\s+pad)"),
    # Smartphones: el catalogo real empieza todos los telefonos con el
    # prefijo "Telefono celular". Exigirlo evita que accesorios, bicicletas,
    # tablets, scooters o relojes caigan aqui solo por compartir una marca.
    # Smartphone standalone / iphone N siguen siendo senales fuertes.
    ReglaCategoria(_CAT_CEL,     "Smartphones",      r"^\s*tel[ée]fono\s+celular\b|^\s*celular\s+\w|\bsmartphone\b|\biphone\s+\d"),
    ReglaCategoria(_CAT_FOTO,    "Cámaras",          r"\bc[áa]mara\s+(?:sony|canon|nikon|fuji|panasonic|fotogr[áa]fica|digital|r[eé]flex|mirrorless|gopro)\b|\blentes?\s+(?:sony|canon|nikon)\b|\bteleobjetivo\b|\btr[ií]pode\s+(?:aluminio|foto|para\s+c[áa]mara)\b|\bflash\s+(?:profesional|para\s+c[áa]mara)\b"),
    ReglaCategoria(_CAT_SEG,     "Cámaras de Seguridad", r"\bc[áa]mara\s+(?:\w+\s+){0,3}(?:de seguridad|ip|wifi|wi[-\s]?fi|domo|vigilancia|inteligente|tapo|ezviz)\b|\b(?:enabot\s+ebo|robot\s+c[aá]mara|home\s+security)\b"),
    ReglaCategoria(_CAT_SEG,     "Alarmas",          r"\b(kit\s+alarma|kit\s+de\s+alarma|kit\s+c[aá]maras?|alarma\s+(?:wifi|wi[-\s]?fi|smart)|sensor (?:pir|magn[eé]tico|de humo|de movimiento|de\s+temperatura|y\s+humedad|de\s+apertura)|bot[oó]n\s+(?:inteligente|de\s+p[aá]nico)|cerradura\s+(?:smart|inteligente|digital))\b"),
    ReglaCategoria(_CAT_HOGAR,   "Smart Home",       r"\b(interruptor(?:es)?\s+(?:\w+\s+)?(?:smart|zigbee|inteligente|wifi)|enchufes?\s+(?:smart|universal\s+smart|placa\s+smart|zigbee)|minienchufes?\s+smart|control\s+remoto\s+ir\s+smart|enchufes?\s+wifi\s+dimax|tapo\s+p\d+)\b"),
    ReglaCategoria(_CAT_MASC,    "Mascotas",         r"\b(mascotas?|perros?|gatos?|fuente\s+de\s+agua\s+(?:smart\s+)?(?:dimax\s+)?para\s+mascota|alimentadores?\s+(?:inteligente\s+|smart\s+)?(?:con\s+c[aá]mara\s+)?(?:smart\s+)?para\s+mascotas?|cama\s+para\s+(?:perro|gato)|correa\s+para\s+(?:perro|gato)|collar\s+para\s+(?:perro|gato)|arenero|rascador|comederos?\s+para\s+mascotas?)\b"),
    ReglaCategoria(_CAT_SEG,     "Cámaras de Seguridad 2", r"\bc[áa]mara\s+smart\s+(?:dimax|con\s+reflectores)\b|\bc[áa]mara\s+con\s+reflectores\b"),
    ReglaCategoria(_CAT_SEG,     "Cerraduras",       r"\b(cerraduras?|candados?|cerrojos?|pasadores?\s+(?:cil[ií]ndrico|pasador)|visor\s+de\s+puerta|bisagras?|pestillo|mirilla)\b"),
    ReglaCategoria(_CAT_SEG,     "Señalización",     r"\btablero\s+plegable\s+piso\s+mojado\b|\bse[ñn]aliz"),

    # --- Audio ---
    ReglaCategoria(_CAT_AUDIO,   "Audífonos",        r"\b(aud[íi]fonos?|auriculares?|earbuds|headphones?|in[-\s]?ear|airpods|galaxy\s+buds\w*)\b"),
    ReglaCategoria(_CAT_AUDIO,   "Parlantes",        r"\b(parlantes?|altavoces?|bocinas?|soundbar|speakers?|minicomponentes?|subwoofer)\b"),
    ReglaCategoria(_CAT_AUDIO,   "Home Theater",     r"\b(home theater|home cinema|minicomponente|microcomponente|cine\s+en\s+casa|bravia\s+theater)\b"),
    ReglaCategoria(_CAT_AUDIO,   "Micrófonos",       r"\b(micr[oó]fono|amplificador (?:est[eé]reo|de audio)|mezclador (?:de )?audio|turntable|tornamesa)\b"),
    ReglaCategoria(_CAT_AUDIO,   "Instrumentos",     r"\b(guitarras?|clarinete|flauta|trompeta|saxof[oó]n|viol[ií]n|viola|bater[íi]a\s+(?:ac[uú]stica|electr[oó]nica)|piano|teclado\s+musical|ukelele|cajaron|mapex)\b"),
    ReglaCategoria(_CAT_AUDIO,   "Soportes",         r"\bsoporte\s+(?:para\s+)?(?:clarinete|flauta|trompeta|saxof[oó]n|viol[ií]n|viola|guitarra|bater[íi]a|micr[oó]fono|teclado|ukelele|iluminaci[oó]n|saxo|partituras?)\b|\bhercules\s+(?:travlite|ds\d|gs\d|ls\d|ms\d|mh\d)"),

    # --- Pequeños electrodomesticos ---
    ReglaCategoria(_CAT_PEQ,     "Licuadoras",       r"\b(licuadora|batidora|mixer|procesador(?:a)?\s+(?:de\s+alimentos|\d+\s+en\s+\d)|extractor(?:a)?\s+(?:de\s+jugos?|nappo|neju)|extractora\b|juguera|picadora|exprimidor(?:a)?|centrifugadora)\b"),
    ReglaCategoria(_CAT_PEQ,     "Cafeteras",        r"\b(cafetera|espresso|molinillo de caf[eé]|tetera el[eé]ctrica|hervidor|set\s+de\s+barismo|sacacorcho\s+el[eé]ctrico)\b"),
    ReglaCategoria(_CAT_PEQ,     "Freidoras",        r"\b(freidora|air\s*fryer)\b"),
    ReglaCategoria(_CAT_PEQ,     "Ollas Eléctricas", r"\b(arrocera|olla arrocera|olla a presi[oó]n|olla el[eé]ctrica|multi[-\s]?olla|sart[eé]n el[eé]ctrica|sandwichera|waflera|waffle|m[aá]quinas?\s+de\s+(?:sopa|pan|helados?|pasta))\b"),
    ReglaCategoria(_CAT_PEQ,     "Tostadoras",       r"\btostador(?:a)?\b"),
    ReglaCategoria(_CAT_PEQ,     "Aspiradoras",      r"\b(aspiradora|aspirador(?:es)?\s+(?:de\s+)?(?:polvo|l[ií]quido|polvo\s+l[ií]quido)|robot aspirador|hidrolavadora|limpiadora de vidrios)\b"),
    ReglaCategoria(_CAT_PEQ,     "Planchas",         r"\b(plancha a vapor|plancha el[eé]ctrica|plancha\s+(?:de\s+ropa|seca\s+y\s+(?:a\s+)?vapor|mq|mq\s+max)|centro de planchado|tabla de planchar|parrilla el[eé]ctrica)\b"),
    ReglaCategoria(_CAT_PEQ,     "Agua",             r"\b(purificador\s+de\s+agua|dispensador\s+(?:el[eé]ctrico\s+)?de\s+agua|hervidor\s+el[eé]ctrico|termo\s+el[eé]ctrico|m[aá]quina\s+gasificadora\s+de\s+agua)\b"),
    ReglaCategoria(_CAT_PEQ,     "Limpieza",         r"\b(cepillos?\s+rotativos?|limpiador\s+el[eé]ctrico)\b"),
    ReglaCategoria(_CAT_PEQ,     "Humidificadores",  r"\b(humidificador(?:es)?)\b"),
    ReglaCategoria(_CAT_PEQ,     "Palomitas",        r"\b(m[aá]quina\s+pipoquera|pipoquera|m[aá]quina\s+de\s+palomitas)\b"),

    # --- Cuidado personal / salud ---
    ReglaCategoria(_CAT_CPER,    "Afeitadoras",      r"\b(afeitadora|rasuradora|recortador(?:a)?|trimmer|corta[\s-]?pelos?|m[áa]quina\s+de\s+cortar\s+cabello|clipper|depiladoras?)\b"),
    ReglaCategoria(_CAT_CPER,    "Cuidado Facial",   r"\b(vaporizador\s+facial|limpiador\s+facial|mascarilla\s+facial|mascarilla\s+coreana|humidificador\s+facial)\b"),
    ReglaCategoria(_CAT_CPER,    "Secadores",        r"\b(secador(?:a)? de (?:pelo|cabello)|secador\s+(?:unibell|ultra|\d+w)|plancha de pelo|rizador|alisadora|ondulador|bucleadora|tratamiento\s+capilar|unibell\s+ultra|photon\s+led)\b"),
    ReglaCategoria(_CAT_CPER,    "Cuidado Bucal",    r"\b(cepillo dental el[eé]ctrico|irrigador|waterpik)\b"),
    ReglaCategoria(_CAT_CPER,    "Perfumería",       r"\b(perfume|colonia|fragancia|eau de (?:toilette|parfum)|\bedt\b|\bedp\b|body\s+spray|deod(?:orante)?|antitranspirante|body\s+mist)\b"),
    ReglaCategoria(_CAT_CPER,    "Manicura",         r"\bset\s+de\s+manicura\b|\bpedicura\b|\bmanicura\b"),
    ReglaCategoria(_CAT_CPER,    "Peso",             r"\bbalanza\s+(?:de\s+)?ba[ñn]o\b|\bbalanza\s+digital\b"),
    ReglaCategoria(_CAT_SALUD,   "Cuidado Salud",    r"\b(ox[ií]metro|term[oó]metro|tensi[oó]metro|gluc[oó]metro|nebulizador|masajeador|almohadilla el[eé]ctrica|pistola\s+(?:sensible\s+)?de\s+masaje|pistola\s+muscular|sillas?\s+de\s+ruedas|electroestimulador|equipo\s+(?:digital\s+)?tens|\btens\s*/?\s*ems\b|cintur[oó]n\s+estimulador|equipo\s+de\s+masaje|hidromasaje\s+(?:para\s+)?pies?|ba[ñn]o\s+para\s+pies?)\b"),
    ReglaCategoria(_CAT_SALUD,   "Básculas",         r"\b(balanzas?\s+(?:de\s+diagn[oó]stico|de\s+vidrio(?:\s+para\s+diagn)?|con\s+dise[ñn]o|con\s+bluetooth|electr[oó]nicas?)|b[aá]sculas?\s+(?:de\s+diagn[oó]stico|digital|electr[oó]nicas?))\b"),

    # --- Niños / juguetes ---
    ReglaCategoria(_CAT_BEBES,   "Coches",           r"\b(coche (?:de paseo|travel system|portabeb[eé]|de muñec)|coche\s+jet|triciclo|bebesit|portabeb[eé]|silla\s+(?:alta|de\s+auto)|andador|corral\s+infantil|balanc[íi]n\s+(?:bebe|beb[eé]|infantil|ni[ñn]o))\b"),
    ReglaCategoria(_CAT_BEBES,   "Bebés",            r"\b(beb[eé]|infantil|cuna|cochecito|pa[ñn]al|biber[oó]n|silla de auto|tasty junior|chupete|sonajero|baranda\s+de\s+seguridad|kit\s+de\s+almuerzo|bouncer|skip\s+hop|tigre\s+de\s+vinil|babyland|dream\s*baby|bright\s*starts?|fisher[-\s]?price|bandeirante|cardoso\s+toys|cotiplas|extractor\s+de\s+leche|calienta\s+biberon|esterilizador\s+(?:de\s+)?biberon|puerta\s+de\s+seguridad(?:\s+\d)?|seguros?\s+d[ae]?\s*\/?\s*ni[ñn]o|seguros?\s+(?:de\s+|para\s+|d?\/?\s*)armario|tapones?\s+protectores?\s+p(?:ara\s+|\/\s*)robacorrientes?|correas?\s+de\s+anclaje\s+para\s+tv|baby\s+einstein|nenuco|bbluv|bolsos?\s+cambiador(?:es)?|set\s+m[eé]dico|ba[ñn]era\s+(?:infantil|burigotto|millenia|bebe|del\s+beb[eé])|coche\s+wagon|baby\s+trend)\b"),
    ReglaCategoria(_CAT_JUGUE,   "Juguetes",         r"\b(juguetes?|mu[ñn]ecos?|mu[ñn]ecas?|peluches?|lego|bloques|juego did[áa]ctico|juego\s+(?:de\s+cartas?|codigo\s+animal|combate\s+estrela|corrida\s+cruzada|de\s+colores?\s+y\s+n[uú]meros?)|monopat[ií]n|scooter|rompecabez|barbie|carritos?\s+de\s+(?:super|muñec|princes|supermercado)|disney\s+princes|xmen|x[-\s]?men|kit\s+\d+\s+juegos?|clementoni|figuras?\s+(?:de\s+)?acci[oó]n|autitos?|plastilinas?|pegatinas?|stickers?|calcoman[íi]as?|cra[-\s]?z[-\s]?art|hasbro|mattel|djeco|stanley\s+jr|rtb\s+stanley|kit\s+(?:creativo|del\s+sistema\s+solar)|juego\s+de\s+bowling|juego\s+comedor\s+de\s+ocho\s+sillas|tablero\s+(?:de\s+)?juego|dino|dinosauri|hot\s*wheels|pala\s+para\s+ni[ñn]os|paola\s+reina|set\s+de\s+manualidades?|bordado|piko\s+piko|transformers|libro\s+(?:animales|cuento|interactivo)|masa\s+(?:moldeable|para\s+modelar)|luke\s+skywalker|star\s+wars|black\s+series|trinca\s+de\s+cores|biopod(?:\s+single)?|silverlit|pais\s+&\s+filhos)\b"),

    # --- Deporte / outdoor ---
    ReglaCategoria(_CAT_DEP,     "Fitness",          r"\b(bicicletas?|caminadora|trotadora|el[íi]ptica|mancuernas?|\bpesas?\b|yoga mat|colchoneta|palas?\s+(?:de\s+|para\s+ni[ñn]os?\s+)?(?:p[áa]del|bullpadel)|raquetas?|gimnasio\s+(?:monark|multifunci|completo)|bandas?\s+(?:para\s+|de\s+)?(?:ejercicio|ejercitarse|ejericicio|resistencia|trx))\b"),
    ReglaCategoria(_CAT_DEP,     "Outdoor",          r"\b(camping|bolsa de dormir|carpa|mochilas?\s+(?:de\s+)?(?:trekking|escolar|con ruedas)?|mochilas?|casco|coolers?|conservadoras?|inflables?|hamacas?|kayak|tabla de surf)\b"),
    ReglaCategoria(_CAT_DEP,     "Ciclismo",         r"\b(neum[aá]ticos?|par\s+de\s+neum[aá]ticos?|maxxis|desllantadores?|desenllantadores?|bomba\s+(?:de\s+|para\s+)?aire\s+(?:bici|bicicleta))\b"),
    ReglaCategoria(_CAT_DEP,     "Acuáticos",        r"\b(gafas\s+(?:de\s+)?buceo|lentes\s+para\s+nataci[oó]n|lentes\s+para\s+natacion|m[áa]scara\s+(?:de\s+|para\s+)?buceo|snorkel|aletas|boya|chaleco salvavida|flotador|salvavidas?|brazalete inflable|inflador|piscina inflable|piscina|set\s+de\s+buceo)\b"),
    ReglaCategoria(_CAT_DEP,     "Pelotas",          r"\bpelotas?\s+(?:de\s+|pl[aá]sticas?|f[úu]tbol|basket|v[óo]ley|plastica)\b"),

    # --- Hogar / muebles ---
    ReglaCategoria(_CAT_MUEBLES, "Colchones",        r"\bcolch[oó]n\b"),
    ReglaCategoria(_CAT_MUEBLES, "Sommiers",         r"\b(somm?ier|respaldo\s+tapizado|cabecera\s+(?:tapizada|cama)|respaldar)\b"),
    ReglaCategoria(_CAT_MUEBLES, "Muebles",          r"\b(sillas?|sillones?|sill[oó]n|sof[aá]s?|mesas?|escritorios?|muebles?|estanter[íi]as?|repisas?|cama(?:s|\s+\d|\s+king|\s+queen)?|ropero|almohadas?|cojin(?:es)?|coj[ií]n|hamper|brizza\s+tela|silla\s+ejecutiva|tela\s+ejecutiva)\b"),
    ReglaCategoria(_CAT_HOGAR,   "Iluminación",      r"\b(l[aá]mparas?|foco\b|luminaria|ara[ñn]a|plafon|bombillo|bombillas?\s+smart|bombillas?\s+(?:tapo|led)|(?:luz|luces)\s+(?:recargables?|led|traseras?|delanteras?))\b"),
    ReglaCategoria(_CAT_HOGAR,   "Decoración",       r"\b(cortina|alfombra|cuadro|espejo|flore(?:ro|s) artificial|organizador|exhibidor|caja fuerte)\b"),
    ReglaCategoria(_CAT_HOGAR,   "Organización",     r"\b(cajas?\s+organizadora|cajas?\s+organiz\s*adoras?|cajas?\s+con\s+tapa\b|cajas?\s+plegables?|cajas?\s+de\s+almacenamiento|basureros?|cubos?\s+de\s+basura|jaboneras?|cepillos?\s+lavaplatos|set\s+de\s+accesorios|canastos?|cestas?\s+(?:de\s+)?(?:algod[oó]n|lavander[ií]a|lavado|para\s+ropa|grande|multiuso|ducha)|cesto[s]?\s+(?:de\s+)?ropa|tendederos?|tendedero\s+(?:de|plegable)|porta\s*(?:cubiertos|utensilios|shampoo|jab[oó]n|papel|toallas|cepillos)|organizadores?|percheros?|colgador(?:es)?\s+de\s+ropa|bandejas?\s+(?:de\s+acr[ií]lico|para\s+huevos|de\s+ducha)|dispensador(?:es)?\s+(?:acr[ií]lico|d[e\/]?\s*jab[oó]n)|set\s+de\s+\d+\s+etiquetas?|etiquetas?\s+adhesivas?|etiquetas?\s+de\s+cables?|meal\s+prep|contenedor(?:es)?\s+(?:de\s+alimentos|de\s+alta\s+resistencia|alimento|inabox)|conjuntos?\s+de\s+\d+\s+accesorios?|bolsas?\s+de\s+(?:lavado|lavander[ií]a?|ropa\s+plegable)|bolsa\s+plegable|estaci[oó]n\s+de\s+lavander[ií]a?|estante\s+(?:expandible|de\s+especias|multiuso)|escurreplatos?|riel\s+(?:de\s+|para\s+|\d+m\s)|kit\s+de\s+closet|zapateros?|cajon\s+de\s+rejilla|rejillas?\s+(?:para\s+zapatero)?|columnas?\s+telesc[oó]pica|soportes?\s+para\s+(?:toallas?|bolsas?|papel|cepillos?|garrafa|iluminaci[oó]n)|soportes?\s+de\s+(?:iluminaci[oó]n|cepillo|acero|papel|toallas?)|soportes?\s+(?:de\s+acero|inox|inoxidable|met[aá]lico|pl[aá]stico)|ganchos?\s+(?:de\s+almacenamiento|para\s+ducha|de\s+acero|de\s+ducha|universales?)|juegos?\s+de\s+\d+\s+ganchos|topes?\s+(?:de\s+puerta|de\s+pared)|pisos?\s+ba[ñn]o|piso\s+ba[ñn]o|almohadillas?\s+de\s+silicona)\b"),
    ReglaCategoria(_CAT_HOGAR,   "Viaje",            r"\b(maletas?|valijas?|equipaje|bolsos?\s+de\s+viaje|set\s+de\s+viaje|estuches?\s+de\s+viaje|mochilas?\s+de\s+viaje)\b"),
    ReglaCategoria(_CAT_HOGAR,   "Baño",             r"\b(grifos?|ducha\s+(?:higi[eé]nica|tipo\s+tel[eé]fono|c\/barra|con\s+barra|de\s+mano|mezcladora)|mezcladora\s+(?:de\s+)?ducha|escobillas?\s+(?:para|de)\s+ba[ñn]o|escobilla\s+para\s+ba[ñn]o|tapa\s+de\s+ba[ñn]o|porta\s*rollos?|barra\s+acero\s+inox\s+d\/seguridad)\b"),
    ReglaCategoria(_CAT_HOGAR,   "Costura",          r"\bm[áa]quinas?\s+(?:de\s+coser|overlock|colleret|collaret|mec[áa]nica|computarizada)\b"),
    ReglaCategoria(_CAT_HOGAR,   "Bricolaje",        r"\blonas?\s+pl[aá]sticas?\b|\bpl[aá]stico\s+rollo\b|\bpintura\s+(?:l[áa]tex|esmalte)\b|\bjuego\s+de\s+abrazaderas?\b"),
    ReglaCategoria(_CAT_COC_MEN, "Utensilios",       r"\b(sart[eé]n|ollas?(?!\s*el[eé]ctrica)|tazas?|platos?|vasos?|copas?\s+\d+\s*pcs|copas?\b|cuchillos?|cuberter[ií]a|cubiertos?|tablas?\s+(?:de\s+)?cocina|fuentes?\s+(?:de\s+)?horno|juegos?\s+de\s+ollas|juegos?\s+de\s+vajilla|vajillas?|tomatodo|termos?\s+(?:\d|tapa|aluminio)|termo\s+\d+l|filtros?\s+(?:de\s+agua|pro\s+aqua)|tarros?\s+para\s+comida|kits?\s+de\s+utensilios|kits?\s+de\s+barbacoa|parrillas?\s+(?:de|para|plancha)|sif[oó]n(?:es)?\s+(?:para\s+)?cremas?|sif[oó]n(?:es)?\s+en\s+aluminio|cortadoras?\s+de\s+fiambres|dispensador(?:es)?\s+(?:de|para)\s+(?:agua|jab[oó]n|jugos?))\b"),
    ReglaCategoria(_CAT_HOGAR,   "Limpieza",         r"\b(escoba|trapeador|detergente|desinfectante|lavandina|limpiador|ducha de mano|mopas?|escobillas?|plumeros?|cepillos?\s+(?:pl[aá]stico|de\s+lavanderia|plasticos?|metal[ií]co|de\s+limpieza|para\s+botellas?)|recogedor(?:es)?|guantes?\s+multiusos?|guantes?\s+(?:quitapolvo|de\s+lim|de\s+nitrilo|de\s+l[aá]tex|latex)|esponjas?\s+(?:multiusos?|de\s+microfibra)|pa[ñn]o\s+(?:microfibra|c\/estropajo)|pa[ñn]os?\s+(?:microfibra|de\s+limpieza)|cubos?\s+(?:p(?:ara\s+|\/\s*)trapear|escurridor|plegables?)|botellas?\s+rociadoras?|absorbente\s+de\s+humedad|abrillantador(?:es)?\s+multiusos?|silicona\s+multiusos?|esmalte\s+de\s+acabados?)\b"),
    ReglaCategoria(_CAT_HOGAR,   "Jardín",           r"\b(mangueras?\s+(?:d[e\/]?\s*jard[ií]n|expandibles?|c\/conexion)|portamangueras?|carro\s+portamanguera|rociador\s+(?:ajustable|de\s+agua)|aspersor(?:es)?|podador(?:a)?|macetas?|tierra\s+para\s+planta|semillas|fertilizante)\b"),
    ReglaCategoria(_CAT_HOGAR,   "Accesorios Baño",  r"\b(toalleros?|porta\s*(?:shampoo|jab[oó]n|cepillos?|toallas?|papel)|dispensador(?:es)?\s+(?:de\s+|d\/|para\s+)?jab[oó]n|dispensador(?:es)?\s+acr[ií]lico|juego\s+de\s+accesorios?\s+de\s+ba[ñn]o|juego\s+de\s+(?:12\s+)?ganchos\s+para\s+ducha|barra\s+(?:acero|de\s+seguridad)|soporte\s+para\s+garrafa|discos?\s+antideslizantes?)\b"),

    # --- Autos / herramientas / otros ---
    ReglaCategoria(_CAT_HERR,    "Herramientas",     r"\b(amoladora|taladro|atornillador|sierras?|motosierras?|bordeadoras?|fumigadoras?|lijadora|compresor|generador|soldador(?:a)?|antorcha(?:s)?|sopletes?|juego de brocas|llave inglesa|pinzas?|alicates?|martillo|destornillador|juego de herramientas|caja de herramientas|cortacesped|cortac[eé]sped|corta[\s-]?setos?|cortasetos?|desbrozadoras?|cortador\s+de\s+cer[aá]mica|cargador\s+(?:para\s+)?bater[íi]as?|bater[íi]a\s+(?:flexvolt|recargable\s+20v|dewalt)|flexvolt|cuchilla\s+para|juego\s+de\s+cuchillas?|rotomartillo|clavos?|tornillos?|arandelas?|cable\s+acero\s+galvanizado|(?:niveles?|nivel)\s+de\s+aluminio|prensas?\s+(?:de\s+)?(?:ajuste|tipo\s+c)|serruchos?|juego\s+\d+\s+dados?|dados?\s+(?:largos|hexagonales|encastre)|bolsa\s+para\s+herramientas?|rueda\s+(?:giratoria|r[ií]gida|tipo\s+esfera)|correas?\s+(?:con\s+)?(?:ratchet|el[aá]stica|ajustables?|de\s+anclaje|elasticas)|correas?\s+de\s+almacenamiento|sujetadores?\s+(?:con\s+hebillas?|multiusos?)|m[aá]quina\s+multiuso|maquina\s+multiuso|goodyear\s+gy\d|echo\s+hca)\b"),
    ReglaCategoria(_CAT_AUTO,    "Accesorios Auto",  r"\b(cubreasientos?|cubre\s+piso|cargador de auto|volante auto|luz delantera|llantas?|cobertor(?:es)?\s+(?:para\s+)?auto|lonas?\s+(?:para\s+)?auto|rueda\s+de\s+auxilio|set\s+pisos?\s+(?:p(?:ara\s+|\/\s*)|de\s+)auto|pisos?\s+p(?:ara\s+|\/\s*)auto|cobertor(?:es)?\s+(?:para\s+)?volante|cables?\s+pasa\s+corriente|correa\s+(?:c\/)?ratchet|correa\s+(?:el[aá]stica\s+)?p(?:ara\s+|\/\s*)remolque)\b"),
    ReglaCategoria("Audio Auto", "Radio Auto",       r"\bradio\s+(?:para\s+)?auto\b|\bradio\s+receptor\s+(?:de\s+medios|multimedia)\b|\bautoradio\b"),
    ReglaCategoria(_CAT_AUTO,    "Vehículos",        r"\b(motocicleta|moto\s+(?:el[eé]ctrica|deportiva)|scooter\s+el[eé]ctric[oa]|patineta\s+el[eé]ctrica)\b"),
    ReglaCategoria(_CAT_RELOJ,   "Relojes",          r"\breloj\s+(?:de\s+(?:hombre|mujer|var[oó]n|dama|caballero|ni[ñn]o|pared)|casio|guess|fossil|seiko|citizen|g[-\s]?shock|anal[oó]gico|digital)\b|\brelojes?\s+(?:casio|qq|guess|fossil|seiko|citizen)\b|^reloj\s+\w"),
    ReglaCategoria(_CAT_ACC_TV,  "Cables",           r"\b(cable hdmi|cable displayport|cable (?:tipo )?c|adaptador\b)\b"),
    ReglaCategoria(_CAT_COMPU,   "Repuestos TV",     r"\btablero\s+principal\s+(?:para\s+)?tv\b|\bbackligh?t\b|\bcontroladora\s+lcd\b"),
]

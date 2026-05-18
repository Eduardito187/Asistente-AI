from __future__ import annotations

import re

# ============================================================================
# DetectorPedidoDetalle: cubre EXHAUSTIVAMENTE las formas que un cliente
# latino/boliviano usa para pedir información detallada sobre un producto.
#
# Categorías cubiertas (cada una con muchas variaciones):
#  1. Pedidos de información explícitos ("contame", "explicame", "info")
#  2. Pedidos de descripción ("describime", "describí", "descripción")
#  3. Pedidos de specs / características ("specs", "ficha", "atributos")
#  4. Comparativos ("compara", "diferencia", "vs", "contra")
#  5. Razón / recomendación ("por qué conviene", "vale la pena", "recomiendas")
#  6. Atributos técnicos como pregunta ("pantalla", "RAM", "GPU", "batería")
#  7. Preguntas directas ("qué procesador tiene", "cuál es la cámara")
#  8. Coloquialismos latinos ("contame", "decime", "mostrame", "fijate")
#  9. Pregunta de uso ("para qué sirve", "es bueno para gaming")
# 10. Pedidos de ampliación ("más info", "expandí", "ampliame")
#
# Filosofía: tolerar tildes ([íi]), plurales (sin \b final cuando aplica),
# conjugaciones argentinas/latinas (-ame/-ate), variantes con/sin "que".
# Mejor falso positivo que falso negativo en este detector — el peor caso
# es que un mensaje sin SKU dispare detalle y se devuelva fallback "no se
# encontró producto", lo cual es benigno.
# ============================================================================

RX_PEDIDO_DETALLE = re.compile(
    r"(?:"

    # ===== 1. INFORMACIÓN EXPLÍCITA =====
    r"\bdetalle"                                  # detalle/detalles
    r"|\bdet[áa]ll[áa](?:s|me|nos|le|lo|la|melo)?\b"  # detállame/detállalo/detallás/detalláme
    r"|\bdetallar(?:me|los?|las?)?\b"              # detallar/detallarme/detallarlo
    r"|\bm[áa]s\s+detalles?"                       # más detalles
    r"|\bme\s+das?\s+(?:m[áa]s\s+)?(?:detalle|info|datos|caracter|ficha)" # me das más datos/info...
    r"|\bm[áa]s\s+info\b"                          # más info
    r"|\bm[áa]s\s+informaci[óo]n"                  # más información
    r"|\binformaci[óo]n\s+(?:de|sobre|adicional|extra|"
    r"completa|total|toda|del|al?\s+respecto)"     # información completa/sobre/del...
    r"|\bdame\s+(?:m[áa]s\s+)?(?:info|detalle|datos|specs?|caracter)"  # dame más info/datos
    r"|\b(?:dime|d[íi]me|decime|dec[íi]me|deci|d[íi])\s+(?:m[áa]s|todo|qu[ée])"
    r"|\bampliar?\s+informaci"                     # ampliar información
    r"|\bampl[ií][áa]?(?:me|nos|lo|la)?\b"          # amplíame/amplía/ampliame
    r"|\bextend[éeí]r?(?:me|nos)?\b"               # extendéme/extender
    r"|\bexpand[ií](?:r|me|t|lo|los|nos)?"         # expandí/expandime/expandir
    r"|\bexpansion"
    r"|\binf[óo]rmame?|\binfo[ée]rmenme?\b"        # infórmame/infórmenme
    r"|\bquiero\s+(?:m[áa]s\s+)?(?:info|datos|detalles|saber|conocer)"
    r"|\bnecesito\s+(?:m[áa]s\s+)?(?:info|datos|detalles|saber|conocer)"
    r"|\bcontame\b|\bcont[áa](?:nos|le|lo|la)?\b|\bcuent[ae]me\b|\bcu[eé]nt[ae](?:nos|le|lo|la|me)\b"
    r"|\bcuenta\s+m[áa]s\b|\bcontame\s+m[áa]s\b"
    r"|\bexpl[ií]c[áa](?:me|nos|le|lo|la|melo)?\b" # explícame/explicame/explicáme
    r"|\bexplicame\b"
    r"|\bexplicar?\b|\bexplicaci[óo]n\b"
    r"|\bexpl[ií]queme\b|\bexpl[íi]calo\b"
    r"|\bh[áa]bl[ae]me\s+(?:de|sobre|del?)"
    r"|\bcoment[áa]me\b|\bcom[ée]ntame\b"

    # ===== 2. DESCRIPCIÓN =====
    r"|\bdescrib[eií](?:me|lo|la|nos|les|mela|melo)?"  # describime/describí/describilo
    r"|\bdescr[ií]be(?:me|lo|la|nos|les)?"          # descríbeme/descríbelo
    r"|\bdescr[ií]b[ií](?:r|melo|mela|me|lo)?"      # describír/describime
    r"|\bdescripci[óo]n"                            # descripción
    r"|\bdescriptiv"

    # ===== 3. SPECS / CARACTERÍSTICAS / FICHA =====
    r"|\bespecificac"                              # especificación/especificaciones
    r"|\bespec\b"
    r"|\bcaracter[íi]stic"                         # característica/características
    r"|\bspecs?\b"
    r"|\bspecifications?\b"                        # specifications (inglés mezclado)
    r"|\batributos?\b"                              # atributos
    r"|\bpropiedad(?:es)?\b"                        # propiedades
    r"|\bprestaciones?\b"                           # prestaciones
    r"|\bficha(?:\s+(?:t[ée]cnica|completa|del?\s+producto))?\b"  # ficha técnica
    r"|\bdatos?\s+(?:del?\s+producto|t[ée]cnicos?|completos?)"
    r"|\btoda(?:s)?\s+(?:sus|las|la|los|el)\s+"
    r"(?:caracter[íi]stic|specs?|especific|funcion|propiedad|"
    r"detalle|atributo|prestaci|funci[óo])"
    r"|\bcomp(?:l|let)et[oa]s?\b"

    # ===== 4. COMPARATIVOS =====
    r"|\b(?:comp[áa]r|compar)(?:[áa]|a|e)(?:r|me|melo|mela|menos|nos|lo|la|los|las|s|n)?\b"
    r"|\bcompar(?:ar|aci[óo]n|ame|ada|ado|amelos)"
    r"|\bcompares?\b"
    r"|\bdiferencia(?:s|le|n)?\b"                  # diferencia/diferencias
    r"|\bdifiere\b"
    r"|\ben\s+qu[ée]\s+(?:se\s+)?(?:diferencia|distingue)"
    r"|\b(?:vs|versus|contra|frente\s+a)\b"        # vs / versus / contra
    r"|\bmejor\s+que\b|\bpeor\s+que\b"
    r"|\b(?:cu[áa]l|qu[ée])\s+es\s+(?:mejor|peor)"
    r"|\bventaja(?:s)?\s+(?:sobre|respecto|frente)"

    # ===== 5. RAZÓN / RECOMENDACIÓN / VALOR =====
    r"|\bpor\s+qu[ée]\b"                           # por qué
    r"|\bporque\s+(?:conviene|me\s+conviene|sirve|elegir|comprar|llevar)"
    r"|\bconviene\s+(?:m[áa]s|mejor|elegir|llevar)?"
    r"|\bvale\s+la\s+pena\b"
    # recomienda/recomiendas/recomiéndame/recomendar/recomendarías/recomendación
    r"|\brecom(?:end|iend)(?:a|as|[áa]s|o|ar|ar[ií]as?|ari?an?|ado|ada|aci[óo]n)?\b"
    r"|\brecom(?:i[ée]nd|i[ée]ndalo|i[ée]ndale)(?:a|me|nos|lo|la|los|melo|mela)?"
    r"|\bme\s+recomien(?:das?|de|den)\b"
    r"|\bventaja|\bbeneficio|\bpros?\s+(?:y|del|y\s+contras)\b|\bfortaleza"
    r"|\bdesventaja|\bdefecto|\bcontra(?:s)?\b|\bdebilidad"
    r"|\bsirve\s+(?:para|de)\b"
    r"|\b(?:es|son|seria)\s+bueno?\s+(?:para|en)"
    r"|\b[uú]til\s+para\b"

    # ===== 6. ATRIBUTOS TÉCNICOS (palabra clave sola = pedido de info) =====
    r"|\bpantalla\b|\bdisplay\b|\bscreen\b"
    r"|\bprocesador|\bcpu\b|\bchip\b|\bn[úu]cleos?\b|\bcore(?:s)?\b"
    r"|\bmemoria\b|\bram\b|\bddr\b"
    r"|\bbater[íi]a|\bautonom[íi]a|\bduraci[óo]n\s+(?:de\s+)?bat|\bmah\b"
    r"|\bc[áa]mara|\bfoto(?:s|graf)?|\bv[íi]deo|\bmegap[íi]xel|\bmp\b"
    r"|\bresoluc(?:i[óo]n)?|\bfhd\b|\b4k\b|\b8k\b|\bfull\s+hd\b|\buhd\b"
    r"|\bpeso\b|\bpesa\b|\bkilos?\b|\bgramos?\b"
    r"|\bteclado|\bkeyboard\b"
    r"|\bconectividad|\bwifi|\bbluetooth|\b5g\b|\b4g\b|\blte\b"
    r"|\bpuerto|\busb(?:-c|-a|3|2)?\b|\bhdmi|\bjack\b|\btype-c\b"
    r"|\bsistema\s+operativo|\bandroid|\bios\b|\bwindows|\bmacos"
    r"|\bgpu\b|\bgr[áa]fic|\bvga\b|\bgeforce|\bradeon|\brtx\b|\bgtx\b"
    r"|\brefresh|\bhz\b|\bhertz|\btasa\s+de\s+refresc"
    r"|\balmacenamiento|\bdisco\b|\bssd\b|\bhdd\b|\bnvme\b|\bcapacidad\b"
    r"|\bgb\s+(?:de\s+)?(?:ram|ssd|disco|memoria|almacenamiento)"
    r"|\btb\b|\bgb\b"
    r"|\bgarant[íi]a"
    r"|\bmodelo\b|\bmarca\b"
    r"|\bcolor\b|\bcolores\b|\btonalidad\b"
    r"|\btama[ñn]o|\bdimensi[óo]n|\bmedida|\bpulgad|\binch"
    r"|\bmaterial|\bfabricaci[óo]n|\bhecho\s+de\b"
    r"|\baccesorios?\s+incluidos?|\bincluye\b|\bviene\s+con\b|\btrae\s+(?:el|incluido)"
    r"|\bcompat(?:ible|ibilidad)\b"
    r"|\bvelocidad\b|\brendimiento\b|\bperformance\b|\bpotencia\b"
    r"|\bfrecuencia\b|\brpm\b|\bvatios?\b|\bwatts?\b|\bw\b"
    r"|\binverter\b|\bno\s+frost\b|\beficiencia\s+energ"
    r"|\bcapacidad\s+(?:litros|kg|carga)"

    # ===== 7. PREGUNTAS DIRECTAS SOBRE ATRIBUTOS =====
    r"|\bqu[ée]\s+(?:procesador|memoria|pantalla|c[áa]mara|"
    r"bater[íi]a|gpu|gr[áa]fica|color|tama[ñn]o|peso|"
    r"resoluci[óo]n|versi[óo]n|sistema|capacidad|"
    r"puertos?|conectividad|garant[íi]a|modelo|incluye|"
    r"trae|pulgadas|hz|ram|ssd|almacenamiento|"
    r"caracter[íi]stica|spec|funci|atributo|prestaci|"
    r"diferencia|ventaja|beneficio)"
    # "cuál es la pantalla / el procesador / etc." — acotado a substantivo de spec
    # para evitar falsos positivos con "cuál es el horario / precio / envío".
    r"|\bcu[áa]l\s+es\s+(?:la|el|su|sus|la\s+mejor)\s+"
    r"(?:procesador|memoria|pantalla|c[áa]mara|bater[íi]a|gpu|gr[áa]fica|"
    r"color|tama[ñn]o|peso|resoluci[óo]n|versi[óo]n|sistema|capacidad|"
    r"diferencia|caracter[íi]stica|spec|atributo|funcion|propiedad|modelo|"
    r"marca|garant[íi]a|ram|ssd|almacenamiento)"
    r"|\bcu[áa]nto(?:s)?\s+(?:gb|tb|mp|hz|w|mah|nucleo|core|ram|"
    r"almacenamiento|memoria|pesa|mide|dura|aguanta)"
    r"|\b(?:tiene|trae|incluye|viene\s+con|posee|cuenta\s+con)\s+\w+"
    r"|\b(?:de\s+qu[ée])\s+(?:color|modelo|tama[ñn]o|"
    r"a[ñn]o|material|tipo)"

    # ===== 8. COLOQUIALISMOS LATINOS / BOLIVIANOS =====
    r"|\bmostr[áa](?:me|nos)?\b"                   # mostrame/mostranos
    r"|\bmu[ée]stra(?:me|nos|le)?\b"               # muéstrame/muéstrale
    r"|\bense[ñn][áa](?:me|nos)?\b|\bens[ée]ñame?\b"
    r"|\bfijate\s+(?:que|si)|\bfij[áa]te\b"
    r"|\brevis[áa]\b|\brevis[ée]me\b"
    r"|\bcheq(?:u[ée]ame|u[éeé]a|uea[lr])"
    r"|\ba\s+ver\s+(?:que|qu[ée]|cu[áa]l|si|si\s+es)"
    r"|\bdejame?\s+ver\b|\bd[ée]jame\s+ver\b"
    r"|\bpas[áa](?:me|nos)?\s+(?:m[áa]s|info|datos|detalles)"
    r"|\bp[áa]same\b"
    r"|\bexpl[áaí]y[ae](?:te|rte)?\b"               # explayate/explayar
    r"|\bdesarroll[áa](?:me|lo)?\b"                # desarrollame
    r"|\bdesglos[áaí]r?\b|\bdesgl[óo]same\b"

    # ===== 9. PREGUNTA DE USO / FUNCIONALIDAD =====
    r"|\bpara\s+qu[ée]\s+(?:sirve|es|funciona|se\s+usa)"
    r"|\bqu[ée]\s+hace\b|\bqu[ée]\s+funci[óo]n"
    r"|\bcomo\s+funciona\b|\bc[óo]mo\s+(?:funciona|opera|trabaja)"
    r"|\bsirve\s+(?:bien|para)\s+\w+"
    r"|\b[ií]deal\s+para\b"

    # ===== 10. AMPLIACIÓN / PROFUNDIDAD =====
    r"|\bm[áa]s\s+(?:profundo|profundamente|en\s+detalle|a\s+fondo)"
    r"|\ben\s+(?:profundidad|detalle)"
    r"|\ba\s+fondo\b"
    r"|\btodo\s+(?:lo\s+)?(?:que|sobre|del?)\b"
    r"|\babs[oóu]lutamente\s+todo\b"

    # ===== 11. PEDIDO INFORMAL VAGO PERO CLARO =====
    r"|\bqu[ée]\s+(?:onda|tal|hay|tenemos)\s+(?:con|de)\b"
    r"|\bc[óo]mo\s+es\s+(?:la\s+cosa|esta?|este|ese)"
    r"|\bqu[ée]\s+m[áa]s\s+(?:sabes|me\s+sabes|tienes|hay|me\s+pod[ée]s)"
    r"|\bcontinu[áa]\b|\bsigue\b|\bsig[áa]\b"
    r"|\bagrega\s+algo\b|\balgo\s+m[áa]s\b"

    r")",
    re.IGNORECASE,
)


class DetectorPedidoDetalle:
    """SRP: decide si el mensaje del cliente es un pedido de información
    detallada sobre un producto, en cualquiera de sus muchas formas
    posibles en español latino (Bolivia/AR/MX/CL/CO/etc.).

    Cubre 11 categorías de pedidos exhaustivamente. Tolerante a tildes,
    plurales, conjugaciones latinoamericanas, coloquialismos."""

    @classmethod
    def es_pedido_detalle(cls, mensaje: str) -> bool:
        if not mensaje:
            return False
        return bool(RX_PEDIDO_DETALLE.search(mensaje))

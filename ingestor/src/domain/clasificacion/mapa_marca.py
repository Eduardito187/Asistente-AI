from __future__ import annotations

from typing import Optional, Tuple

_JUGUE = "Juguetería"
_BEBES = "Bebés"
_HERR = "Herramientas"
_MUEBLES = "Muebles"
_CPER = "Cuidado Personal"
_COC_MEN = "Cocina Menor"
_DEP = "Deportes"
_HOGAR = "Hogar"
_PEQ = "Pequeños Electrodomésticos"
_AUDIO = "Audio"
_COMPU = "Computación"
_RELOJ = "Relojería"
_SALUD = "Salud"
_COCINA = "Cocina"

_SUB_JUGUETES = "Juguetes"
_SUB_ACCESORIOS = "Accesorios"
_SUB_COCHES = "Coches"
_SUB_SEGURIDAD = "Seguridad"
_SUB_SOMMIERS = "Sommiers"
_SUB_SECADORES = "Secadores"
_SUB_UTENSILIOS = "Utensilios"
_SUB_OUTDOOR = "Outdoor"
_SUB_ACUATICOS = "Acuáticos"
_SUB_DECORACION = "Decoración"
_SUB_ORGANIZACION = "Organización"
_SUB_COSTURA = "Costura"
_SUB_INSTRUMENTOS = "Instrumentos"
_SUB_LIMPIEZA = "Limpieza"
_SUB_REDES = "Redes"
_SUB_COMPU_ACC = "Accesorios"
_SUB_BANO = "Accesorios Baño"
_SUB_JARDIN = "Jardín"
_SUB_VIAJE = "Viaje"


class MapaMarca:
    """Fallback por marca: asigna categoria cuando una marca es mono-categoria.

    Solo incluir marcas cuyos productos pertenecen casi exclusivamente a una
    categoria. Marcas ambiguas (Sony, Samsung, LG) NO deben estar aqui.
    """

    _MAPA: dict[str, Tuple[str, str]] = {
        # Juguetería
        "djeco": (_JUGUE, _SUB_JUGUETES),
        "hasbro": (_JUGUE, _SUB_JUGUETES),
        "mattel": (_JUGUE, _SUB_JUGUETES),
        "cra-z-art": (_JUGUE, _SUB_JUGUETES),
        "cra z art": (_JUGUE, _SUB_JUGUETES),
        "stanley jr": (_JUGUE, _SUB_JUGUETES),
        "cardoso toys": (_JUGUE, _SUB_JUGUETES),
        "cotiplas": (_JUGUE, _SUB_JUGUETES),
        "clementoni": (_JUGUE, _SUB_JUGUETES),
        "ses creative": (_JUGUE, _SUB_JUGUETES),
        "playmobil": (_JUGUE, _SUB_JUGUETES),
        "hot wheels": (_JUGUE, _SUB_JUGUETES),
        "transformers": (_JUGUE, _SUB_JUGUETES),
        # Bebés
        "skip hop": (_BEBES, _SUB_ACCESORIOS),
        "bright starts": (_BEBES, _SUB_ACCESORIOS),
        "bright start": (_BEBES, _SUB_ACCESORIOS),
        "bandeirante": (_BEBES, _SUB_COCHES),
        "bebesit": (_BEBES, _SUB_COCHES),
        "maxi cosi": (_BEBES, _SUB_COCHES),
        "infanti": (_BEBES, _SUB_COCHES),
        "graco": (_BEBES, _SUB_COCHES),
        "joie": (_BEBES, _SUB_COCHES),
        "dream baby": (_BEBES, _SUB_SEGURIDAD),
        "fisher price": (_BEBES, _SUB_ACCESORIOS),
        "baby einstein": (_BEBES, _SUB_ACCESORIOS),
        # Herramientas
        "dewalt": (_HERR, _HERR),
        "black and decker": (_HERR, _HERR),
        "stanley": (_HERR, _HERR),
        "makita": (_HERR, _HERR),
        "bosch power tools": (_HERR, _HERR),
        "tolsen": (_HERR, _HERR),
        "dowen pagio": (_HERR, _HERR),
        "shindaiwa": (_HERR, _HERR),
        # Muebles
        "maxi king": (_MUEBLES, _SUB_SOMMIERS),
        "nueva era": (_MUEBLES, _SUB_SOMMIERS),
        "plaxmetal": (_MUEBLES, "Sillas"),
        # Cuidado personal
        "babylisspro": (_CPER, _SUB_SECADORES),
        "babyliss": (_CPER, _SUB_SECADORES),
        "ga.ma": (_CPER, _SUB_SECADORES),
        "gama": (_CPER, _SUB_SECADORES),
        "remington": (_CPER, _SUB_SECADORES),
        # Cocina Menor
        "tramontina": (_COC_MEN, _SUB_UTENSILIOS),
        "melitta": (_COC_MEN, _SUB_UTENSILIOS),
        "bohlier": (_COC_MEN, _SUB_UTENSILIOS),
        "peabody": (_COC_MEN, _SUB_UTENSILIOS),
        "sanremo": (_COC_MEN, _SUB_UTENSILIOS),
        "metvisa": (_COC_MEN, _SUB_UTENSILIOS),
        "rubbermaid": (_COC_MEN, _SUB_UTENSILIOS),
        # Deportes
        "bullpadel": (_DEP, "Fitness"),
        "explorer apolo": (_DEP, _SUB_OUTDOOR),
        "igloo": (_DEP, _SUB_OUTDOOR),
        "intex": (_DEP, _SUB_ACUATICOS),
        "bestway": (_DEP, _SUB_ACUATICOS),
        # Hogar / limpieza / organizacion / bano
        "karcher": (_PEQ, "Aspiradoras"),
        "hesperide": (_HOGAR, _SUB_DECORACION),
        "atmosphera": (_HOGAR, _SUB_DECORACION),
        "living accents": (_HOGAR, _SUB_ORGANIZACION),
        "tendance": (_HOGAR, _SUB_ORGANIZACION),
        "diamond visions": (_HOGAR, _SUB_LIMPIEZA),
        "home plus": (_HOGAR, _SUB_LIMPIEZA),
        "wonder house": (_HOGAR, _SUB_LIMPIEZA),
        "ordene": (_HOGAR, _SUB_ORGANIZACION),
        "flex": (_HOGAR, _SUB_ORGANIZACION),
        "avery": (_HOGAR, _SUB_ORGANIZACION),
        "idesign": (_HOGAR, _SUB_BANO),
        "metaltru": (_HOGAR, _SUB_BANO),
        "metraltru": (_HOGAR, _SUB_BANO),
        "green center": (_HOGAR, _SUB_JARDIN),
        "grow": (_HOGAR, _SUB_JARDIN),
        # Costura
        "janome": (_HOGAR, _SUB_COSTURA),
        "brother": (_HOGAR, _SUB_COSTURA),
        # Audio
        "mapex": (_AUDIO, _SUB_INSTRUMENTOS),
        "boya": (_AUDIO, "Micrófonos"),
        "fender": (_AUDIO, _SUB_INSTRUMENTOS),
        "hercules": (_AUDIO, "Soportes"),
        "tama": (_AUDIO, _SUB_INSTRUMENTOS),
        # Computación
        "nexxt": (_COMPU, _SUB_REDES),
        "cudy": (_COMPU, _SUB_REDES),
        "broadlink": (_COMPU, _SUB_REDES),
        "ugreen": (_COMPU, _SUB_COMPU_ACC),
        "klip xtreme": (_COMPU, _SUB_COMPU_ACC),
        "targus": (_COMPU, _SUB_COMPU_ACC),
        "argom": (_COMPU, _SUB_COMPU_ACC),
        "havit": (_COMPU, _SUB_COMPU_ACC),
        # Pequeños electrodomésticos
        "taurus": (_PEQ, "Licuadoras"),
        # Cocina
        "ciarra": (_COCINA, "Campanas"),
        # Salud
        "beurer": (_SALUD, "Cuidado Salud"),
        # Relojería
        "guess": (_RELOJ, "Relojes"),
        # Maletas
        "totto": (_HOGAR, _SUB_VIAJE),
        "rayatta": (_HOGAR, _SUB_VIAJE),
    }

    @classmethod
    def resolver(cls, marca: Optional[str]) -> Optional[Tuple[str, str]]:
        if not marca:
            return None
        clave = marca.strip().lower()
        return cls._MAPA.get(clave)

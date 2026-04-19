from __future__ import annotations

from typing import Dict, Tuple


class MapaProductType:
    """Mapea el campo `product_type` del feed Meta/Facebook a
    (categoria, subcategoria) canonicas de Dismac.

    El feed trae valores muy heterogeneos: algunos ya son categorias utiles
    (Televisores, Celulares, Licuadoras), otros son bolsas genericas que no
    aportan (Marketplace Products, Novedades, vacio). Para los utiles este
    mapa evita tener que inferirlos desde el titulo con regex.
    """

    GENERICOS: frozenset[str] = frozenset({
        "", "marketplace products", "¡exclusivos online!",
        "exclusivos online", "novedades", "zona outlet",
    })

    # Claves comparadas en lowercase. Mantener ordenado por categoria canonica.
    MAPA: Dict[str, Tuple[str, str]] = {
        # Televisores y accesorios
        "televisores":                 ("Televisores", "Smart TV"),
        "accesorios tv & video":       ("Accesorios TV", "Accesorios TV"),
        "home theaters":               ("Audio", "Home Theater"),
        "equipo de sonido":            ("Audio", "Equipo de Sonido"),
        "monitores y proyectores":     ("Computación", "Monitores"),
        "radio para autos":            ("Audio Auto", "Car Audio"),

        # Celulares / smartwatches / tablets
        "celulares":                   ("Celulares", "Smartphones"),
        "accesorios telefonía":        ("Celulares", "Accesorios"),
        "smart watch":                 ("Smartwatch", "Smartwatch"),
        "tablets":                     ("Tablets", "Tablets"),

        # Audio
        "audífonos":                   ("Audio", "Audífonos"),
        "parlantes":                   ("Audio", "Parlantes"),
        "parlantes portátiles":        ("Audio", "Parlantes Portátiles"),
        "parlante portátiles":         ("Audio", "Parlantes Portátiles"),

        # Computación
        "computadoras":                ("Laptops", "Notebooks"),
        "accesorios computación":      ("Computación", "Accesorios"),
        "impresión":                   ("Impresión", "Impresoras"),

        # Gaming / foto / seguridad
        "accesorios videojuegos":      ("Gaming", "Accesorios"),
        "consolas":                    ("Gaming", "Consolas"),
        "cámaras fotográficas y filmación": ("Fotografía", "Cámaras"),
        "camara seguridad":            ("Seguridad", "Cámaras de Seguridad"),
        "caja fuerte":                 ("Seguridad", "Cajas Fuerte"),

        # Climatización
        "tipo split":                  ("Climatización", "Aire Acondicionado"),
        "climatizador":                ("Climatización", "Climatizador"),
        "ventiladores":                ("Climatización", "Ventiladores"),
        "purificadores":               ("Climatización", "Purificadores"),
        "calefones":                   ("Climatización", "Calefones"),
        "termotanques":                ("Climatización", "Termotanques"),
        "calefones y termotanques":    ("Climatización", "Calefones"),
        "duchas":                      ("Climatización", "Duchas Eléctricas"),

        # Refrigeración
        "frio seco":                   ("Refrigeración", "Refrigeradores"),
        "frio conv":                   ("Refrigeración", "Refrigeradores"),
        "semi seco":                   ("Refrigeración", "Refrigeradores"),
        "horizontales":                ("Refrigeración", "Congeladores"),
        "frigobar":                    ("Refrigeración", "Frigobar"),
        "conservadores de alimentos":  ("Refrigeración", "Conservadores"),
        "cooler":                      ("Refrigeración", "Cooler"),
        "enfriadores de sobremesa":    ("Refrigeración", "Enfriadores"),

        # Lavado
        "lavadoras":                   ("Lavado", "Lavadoras"),
        "secadoras":                   ("Lavado", "Secadoras"),
        "lava/seca":                   ("Lavado", "Lavasecadoras"),
        "planchas":                    ("Lavado", "Planchas"),

        # Cocina mayor
        "cocinas":                     ("Cocina", "Cocinas"),
        "encimeras":                   ("Cocina", "Encimeras"),
        "micr conv":                   ("Cocina", "Microondas"),
        "micr grill":                  ("Cocina", "Microondas"),
        "campanas":                    ("Cocina", "Campanas"),

        # Pequeños electrodomésticos
        "licuadoras":                  ("Pequeños Electrodomésticos", "Licuadoras"),
        "batidoras":                   ("Pequeños Electrodomésticos", "Batidoras"),
        "mixers":                      ("Pequeños Electrodomésticos", "Mixers"),
        "extractoras y exprimidores":  ("Pequeños Electrodomésticos", "Extractores"),
        "picadoras":                   ("Pequeños Electrodomésticos", "Picadoras"),
        "freidoras":                   ("Pequeños Electrodomésticos", "Freidoras"),
        "tostadoras":                  ("Pequeños Electrodomésticos", "Tostadoras"),
        "sandwicheras y parillas":     ("Pequeños Electrodomésticos", "Sandwicheras"),
        "cafeteras":                   ("Pequeños Electrodomésticos", "Cafeteras"),
        "teteras y cafeteras":         ("Pequeños Electrodomésticos", "Cafeteras"),
        "de goteo":                    ("Pequeños Electrodomésticos", "Cafeteras"),
        "molinillo de cafe":           ("Pequeños Electrodomésticos", "Cafeteras"),
        "aspiradoras":                 ("Pequeños Electrodomésticos", "Aspiradoras"),
        "accesorios aspirado y limpieza": ("Pequeños Electrodomésticos", "Aspiradoras"),
        "hidrolavadoras":              ("Pequeños Electrodomésticos", "Hidrolavadoras"),
        "ollas":                       ("Pequeños Electrodomésticos", "Ollas Eléctricas"),
        "juego de ollas":              ("Cocina Menor", "Ollas"),
        "sartenes":                    ("Cocina Menor", "Sartenes"),
        "wok":                         ("Cocina Menor", "Wok"),
        "parrillas":                   ("Cocina Menor", "Parrillas"),
        "churrasco":                   ("Cocina Menor", "Parrillas"),
        "cubiertos":                   ("Cocina Menor", "Cubiertos"),
        "cuchillería y tablas":        ("Cocina Menor", "Cuchillería"),
        "utensilios de cocina":        ("Cocina Menor", "Utensilios"),
        "vasos y copas":               ("Cocina Menor", "Vasos y Copas"),
        "fuentes y asaderas":          ("Cocina Menor", "Fuentes"),
        "termos":                      ("Cocina Menor", "Termos"),
        "repostería y cocina creativa": ("Cocina Menor", "Repostería"),

        # Cuidado personal
        "cuidado personal":            ("Cuidado Personal", "Cuidado Personal"),
        "cortapelos y afeitadoras":    ("Cuidado Personal", "Afeitadoras"),
        "alisadoras":                  ("Cuidado Personal", "Alisadoras"),
        "onduladores":                 ("Cuidado Personal", "Onduladores"),

        # Hogar / muebles
        "colchones":                   ("Muebles", "Colchones"),
        "almohadas":                   ("Muebles", "Almohadas"),
        "respaldares":                 ("Muebles", "Respaldares"),
        "bases":                       ("Muebles", "Bases de Cama"),
        "muebles de exterior":         ("Muebles", "Muebles de Exterior"),
        "exhibidores":                 ("Muebles", "Exhibidores"),

        # Herramientas
        "herramientas":                ("Herramientas", "Herramientas"),
        "herramientas manuales":       ("Herramientas", "Herramientas Manuales"),
        "herramientas para jardinería": ("Herramientas", "Jardinería"),
        "jardinería":                  ("Herramientas", "Jardinería"),
        "taladros percutores":         ("Herramientas", "Taladros"),
        "amoladoras":                  ("Herramientas", "Amoladoras"),
        "caja de herramientas":        ("Herramientas", "Caja de Herramientas"),
        "juego de herramientas":       ("Herramientas", "Juegos de Herramientas"),

        # Outdoor / deporte
        "bicicletas":                  ("Deportes", "Bicicletas"),
        "accesorios para camping":     ("Deportes", "Camping"),
        "piscina e inflables":         ("Deportes", "Piscinas"),
        "mochilas":                    ("Deportes", "Mochilas"),

        # Autos / moto
        "accesorios de motos":         ("Automotriz", "Motos"),
        "mecanico":                    ("Automotriz", "Mecánico"),
        "mecánica alta":               ("Automotriz", "Mecánico"),

        # Clásicas = olleria tradicional (Ollas no electricas)
        "clásicas":                    ("Cocina Menor", "Ollas"),
        "inox":                        ("Cocina Menor", "Inox"),
        "plastico":                    ("Cocina Menor", "Plástico"),
    }

    @classmethod
    def resolver(cls, product_type: str | None) -> Tuple[str, str] | None:
        """Devuelve (categoria, subcategoria) si el product_type es util.
        Retorna None para valores genericos (Marketplace, Novedades, vacio)
        para que el caller caiga en el clasificador por regex."""
        if product_type is None:
            return None
        clave = product_type.strip().lower()
        if clave in cls.GENERICOS:
            return None
        return cls.MAPA.get(clave)

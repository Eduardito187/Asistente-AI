from __future__ import annotations

import re


class DetectorMultipleProductos:

    _CATEGORIAS = [
        "laptop", "laptops",
        "celular", "celulares", "smartphone", "smartphones",
        "televisor", "televisores", "tv", "tele",
        "lavadora", "lavadoras",
        "refrigerador", "refrigeradores", "refri", "nevera",
        "tablet", "tablets",
        "audífonos", "audifonos", "auriculares",
        "mouse",
        "teclado", "teclados",
        "cámara", "camara", "cámaras", "camaras",
        "impresora", "impresoras",
        "microondas",
        "licuadora", "licuadoras",
        "monitor", "monitores",
        "parlante", "parlantes", "bocina", "bocinas",
        r"disco\s+duro", "ssd",
        r"memoria\s+ram", "ram",
        "procesador", "procesadores",
        r"tarjeta\s+gráfica", r"tarjeta\s+grafica", "gpu",
    ]

    _PATRON_CATEGORIAS = re.compile(
        r"\b(" + "|".join(_CATEGORIAS) + r")\b",
        re.IGNORECASE,
    )

    _PATRON_MULTIPLE_CONJUNCION = re.compile(
        r"\b(busco|necesito|quiero|dame|muéstrame|muestrame)\b.{1,60}"
        r"\b(y\s+(también|tambien|además|ademas|un|una|el|la)?\b|"
        r"tanto\s+\w+\s+como|además\s+del?|ademas\s+del?)\b",
        re.IGNORECASE,
    )

    _PATRON_LISTA_Y = re.compile(
        r"\b(\w+)\s+y\s+(un|una|el|la)?\s*(\w+)\s+(para|y|,)\b",
        re.IGNORECASE,
    )

    @classmethod
    def es_busqueda_multiple(cls, mensaje: str) -> bool:
        categorias = cls.productos_mencionados(mensaje)
        if len(categorias) >= 2:
            return True
        return bool(cls._PATRON_MULTIPLE_CONJUNCION.search(mensaje))

    @classmethod
    def productos_mencionados(cls, mensaje: str) -> list[str]:
        matches = cls._PATRON_CATEGORIAS.findall(mensaje)
        vistos: list[str] = []
        normalizados: set[str] = set()
        for m in matches:
            clave = m.lower().strip()
            if clave not in normalizados:
                normalizados.add(clave)
                vistos.append(m)
        return vistos

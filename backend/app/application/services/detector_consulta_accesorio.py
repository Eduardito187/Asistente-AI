from __future__ import annotations

from ...domain.shared.normalizacion import NormalizadorTexto


class DetectorConsultaAccesorio:
    """SRP: decide si una consulta apunta a productos accesorios.

    Se usa para permitir que una busqueda muestre accesorios cuando el cliente
    los pide explicitamente (ej. "correa smartwatch", "funda iphone") y para
    filtrarlos en caso contrario (asi "smartwatch" no mezcla correas)."""

    _PALABRAS_ACCESORIO: frozenset[str] = frozenset({
        "correa", "correas", "funda", "fundas", "carcasa", "carcasas",
        "mica", "micas", "estuche", "estuches", "protector",
        "cargador", "cargadores", "adaptador", "adaptadores",
        "cable", "cables", "soporte", "soportes",
        "cartucho", "cartuchos", "toner", "toners", "tinta", "tintas",
        "accesorio", "accesorios",
        "repuesto", "repuestos", "reemplazo",
        "filtro", "filtros", "pelicula", "peliculas",
        "pad", "mousepad", "stylus", "lapiz", "pencil",
        "dock", "bateria", "memoria",
    })

    _SUBCATEGORIAS_ACCESORIO: frozenset[str] = frozenset({
        "accesorios", "accesorios auto", "accesorios bano",
        "accesorios tv", "cables", "control remoto", "soportes",
        "tv stick", "repuestos tv",
    })

    _CATEGORIAS_ACCESORIO: frozenset[str] = frozenset({
        "accesorios tv",
    })

    @classmethod
    def es_consulta_accesorio(
        cls,
        query: str | None,
        categoria: str | None = None,
        subcategoria: str | None = None,
    ) -> bool:
        if subcategoria and NormalizadorTexto.normalizar(subcategoria) in cls._SUBCATEGORIAS_ACCESORIO:
            return True
        if categoria and NormalizadorTexto.normalizar(categoria) in cls._CATEGORIAS_ACCESORIO:
            return True
        if not query:
            return False
        tokens = NormalizadorTexto.normalizar(query).split()
        return any(t in cls._PALABRAS_ACCESORIO for t in tokens)

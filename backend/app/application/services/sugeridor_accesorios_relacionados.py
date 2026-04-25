from __future__ import annotations

from ...domain.productos import Producto
from ...domain.shared.normalizacion import NormalizadorTexto
from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery


class SugeridorAccesoriosRelacionados:
    """SRP: dada una lista de productos principales, propone accesorios de la
    misma subcategoria/categoria como cross-sell.

    Para categorias donde el accesorio depende del modelo (correas de
    smartwatch, fundas de celular), exige match de marca o familia. Para
    el resto (mochilas de laptop, cables de TV, organizadores de heladera),
    devuelve el pool sin filtrar — son universales."""

    LIMITE_DEFAULT = 3
    _POOL_MULT = 4

    # Categorias donde el accesorio es especifico del modelo: aqui la funda/
    # correa de otra marca no sirve y preferimos 0 sugeridos a una incompatible.
    _CATEGORIAS_MARCA_ESTRICTA: frozenset[str] = frozenset({
        "smartwatch", "relojes", "smartwatches", "wearables",
    })

    # Mapa: categoria del producto principal -> categorias donde buscar sus
    # accesorios. Cubre el caso donde los accesorios viven en otra categoria
    # del catalogo (ej. TVs en "Televisores" y sus cables/soportes en "Accesorios TV").
    _CATEGORIAS_ACCESORIOS_RELACIONADAS: dict[str, tuple[str, ...]] = {
        "televisores":                  ("Accesorios TV", "Televisores"),
        "laptops":                      ("Laptops", "Computación"),
        "computacion":                  ("Computación", "Laptops"),
        "celulares":                    ("Celulares",),
        "smartphones":                  ("Celulares",),
        "refrigeracion":                ("Refrigeración", "Hogar"),
        "cocina menor":                 ("Cocina", "Cocina Menor"),
        "cocina":                       ("Cocina", "Cocina Menor"),
        "pequenos electrodomesticos":   ("Cocina", "Pequeños Electrodomésticos"),
        "audio":                        ("Audio", "Celulares"),
        "gaming":                       ("Gaming", "Computación"),
        "tablets":                      ("Tablets", "Celulares"),
        "climatizacion":                ("Climatización", "Hogar"),
        "cuidado personal":             ("Cuidado Personal",),
        "juguetes":                     ("Juguetería",),
        "bebes":                        ("Bebés",),
        "deportes":                     ("Deportes",),
    }

    def __init__(self, buscar: BuscarProductosHandler) -> None:
        self._buscar = buscar

    def sugerir(
        self,
        principales: list[Producto],
        categoria: str | None = None,
        subcategoria: str | None = None,
        limite: int = LIMITE_DEFAULT,
    ) -> list[Producto]:
        if not principales:
            return []
        cat = categoria or principales[0].categoria
        subcat = subcategoria or principales[0].subcategoria
        if not (cat or subcat):
            return []
        skus_excluir = tuple(str(p.sku) for p in principales)
        pool, nivel = self._obtener_pool(cat, subcat, skus_excluir, limite)
        if not pool:
            return []
        # nivel 1 = misma cat+subcat (accesorios universales ok sin filtro marca/familia)
        # nivel 2 = solo cat (puede incluir accesorios de otras subcats irrelevantes)
        # nivel 3 = categoria relacionada (distancia mayor, filtro estricto)
        amplio = nivel >= 2
        if amplio or self._requiere_marca_estricta(cat, subcat):
            return self._filtrar_compatibles(pool, principales)[:limite]
        priorizados = self._filtrar_compatibles(pool, principales)
        skus_priorizados = {str(p.sku) for p in priorizados}
        resto = [p for p in pool if str(p.sku) not in skus_priorizados]
        return (priorizados + resto)[:limite]

    def _obtener_pool(
        self,
        cat: str | None,
        subcat: str | None,
        skus_excluir: tuple[str, ...],
        limite: int,
    ) -> tuple[list[Producto], int]:
        """Fallback progresivo devolviendo (pool, nivel):
          nivel 1: cat+subcat (accesorios especificos del tipo de producto)
          nivel 2: solo cat (accesorios del rubro pero otra subcat)
          nivel 3: categorias relacionadas del mapa
        Niveles 2 y 3 requieren filtro estricto por marca/familia."""
        pool_limite = limite * self._POOL_MULT
        if cat and subcat:
            pool = self._buscar_accesorios(cat, subcat, skus_excluir, pool_limite)
            if pool:
                return pool, 1
        if cat:
            pool = self._buscar_accesorios(cat, None, skus_excluir, pool_limite)
            if pool:
                return pool, 2
        for cat_rel in self._categorias_relacionadas(cat):
            pool = self._buscar_accesorios(cat_rel, None, skus_excluir, pool_limite)
            if pool:
                return pool, 3
        return [], 0

    def _buscar_accesorios(
        self,
        categoria: str,
        subcategoria: str | None,
        skus_excluir: tuple[str, ...],
        limite: int,
    ) -> list[Producto]:
        return self._buscar.ejecutar(
            BuscarProductosQuery(
                categoria=categoria,
                subcategoria=subcategoria,
                solo_con_stock=True,
                solo_accesorios=True,
                excluir_skus=skus_excluir,
                limite=limite,
            )
        )

    @classmethod
    def _categorias_relacionadas(cls, categoria: str | None) -> tuple[str, ...]:
        if not categoria:
            return ()
        clave = NormalizadorTexto.normalizar(categoria)
        relacionadas = cls._CATEGORIAS_ACCESORIOS_RELACIONADAS.get(clave, ())
        # Nunca devolver la misma categoria (ya se probo antes).
        return tuple(c for c in relacionadas if NormalizadorTexto.normalizar(c) != clave)

    @classmethod
    def _requiere_marca_estricta(cls, categoria: str | None, subcategoria: str | None) -> bool:
        for valor in (categoria, subcategoria):
            if valor and NormalizadorTexto.normalizar(valor) in cls._CATEGORIAS_MARCA_ESTRICTA:
                return True
        return False

    @classmethod
    def _filtrar_compatibles(
        cls, pool: list[Producto], principales: list[Producto]
    ) -> list[Producto]:
        """Devuelve solo accesorios compatibles por marca o por tokens del
        nombre del principal. Si no hay ninguno compatible, devuelve lista
        vacia: sugerir accesorios de otra marca (ej. correa Samsung para un
        Apple Watch) es peor que no sugerir nada."""
        marcas = {(p.marca or "").lower() for p in principales if p.marca}
        tokens_familia = cls._tokens_familia(principales)
        if not marcas and not tokens_familia:
            return pool
        return [
            acc for acc in pool
            if cls._es_compatible(acc, marcas, tokens_familia)
        ]

    @staticmethod
    def _tokens_familia(principales: list[Producto]) -> set[str]:
        """Extrae tokens distintivos del nombre del producto principal (ej.
        'galaxy', 'watch7', 'iphone', 'ipad') ignorando palabras muy comunes."""
        genericas = {
            "smartwatch", "reloj", "telefono", "celular", "laptop", "notebook",
            "watch", "phone", "tablet", "televisor", "auriculares", "audifono",
            "color", "negro", "blanco", "gris", "azul", "rojo", "rosa", "verde",
            "crema", "azabache", "medianoche", "medianoch", "oscuro",
            "bluetooth", "pulgadas", "para", "con", "sin", "los", "las",
            "hombre", "mujer", "nino", "nina", "unisex", "serie", "generacion",
            "bateria", "cargador", "bocina",
        }
        tokens: set[str] = set()
        for p in principales:
            for tok in NormalizadorTexto.normalizar(p.nombre).split():
                if len(tok) >= 4 and tok not in genericas:
                    tokens.add(tok)
        return tokens

    @staticmethod
    def _es_compatible(
        acc: Producto, marcas_principales: set[str], tokens_familia: set[str]
    ) -> bool:
        if acc.marca and acc.marca.lower() in marcas_principales:
            return True
        nombre_norm = NormalizadorTexto.normalizar(acc.nombre)
        return any(tok in nombre_norm for tok in tokens_familia)

from __future__ import annotations

from ...domain.productos import Producto
from ...domain.shared.normalizacion import NormalizadorTexto
from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery


class SugeridorAccesoriosRelacionados:
    """SRP: dada una lista de productos principales, propone accesorios de la
    misma subcategoria/categoria como cross-sell. Prioriza accesorios cuya marca
    o familia (por tokens del nombre) coincide con los principales — evita
    sugerir correa Galaxy cuando el cliente vio un Apple Watch."""

    LIMITE_DEFAULT = 3
    _POOL_MULT = 4

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
        pool = self._buscar.ejecutar(
            BuscarProductosQuery(
                categoria=cat,
                subcategoria=subcat,
                solo_con_stock=True,
                solo_accesorios=True,
                excluir_skus=skus_excluir,
                limite=limite * self._POOL_MULT,
            )
        )
        return self._priorizar_por_marca_o_familia(pool, principales)[:limite]

    @classmethod
    def _priorizar_por_marca_o_familia(
        cls, pool: list[Producto], principales: list[Producto]
    ) -> list[Producto]:
        """Reordena el pool: primero los accesorios compatibles con la marca o
        tokens del producto principal (ej. 'galaxy watch7' matchea correas
        'para galaxy watch7'); el resto como fallback al final."""
        marcas = {(p.marca or "").lower() for p in principales if p.marca}
        tokens_familia = cls._tokens_familia(principales)
        compatibles: list[Producto] = []
        resto: list[Producto] = []
        for acc in pool:
            if cls._es_compatible(acc, marcas, tokens_familia):
                compatibles.append(acc)
            else:
                resto.append(acc)
        return compatibles + resto

    @staticmethod
    def _tokens_familia(principales: list[Producto]) -> set[str]:
        """Extrae tokens distintivos del nombre del producto principal (ej.
        'galaxy', 'watch7', 'iphone', 'ipad') ignorando palabras muy comunes."""
        genericas = {
            "smartwatch", "reloj", "telefono", "celular", "laptop", "notebook",
            "color", "negro", "blanco", "gris", "azul", "rojo", "rosa", "verde",
            "bluetooth", "pulgadas", "para", "con", "sin", "de", "el", "la",
            "hombre", "mujer", "nino", "nina", "unisex", "s/m", "m/l",
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

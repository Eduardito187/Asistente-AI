from __future__ import annotations

from dataclasses import dataclass

from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery
from ..queries.comparar_productos import CompararProductosHandler, CompararProductosQuery
from ..queries.comparar_productos.result import ResultadoCompararProductos
from ..queries.resolver_categoria_sinonimo import (
    ResolverCategoriaSinonimoHandler,
    ResolverCategoriaSinonimoQuery,
)
from .detector_comparacion_explicita import ComparacionExplicita
from .renderizador_tabla_comparacion import RenderizadorTablaComparacion


@dataclass(frozen=True)
class RespuestaComparacionExplicita:
    """Texto ya formateado con la tabla markdown + conclusión, listo para
    devolver sin pasar por el LLM."""

    texto: str
    resultado: ResultadoCompararProductos


class ResponderComparacionExplicita:
    """SRP: dado un ComparacionExplicita (2+ fragmentos tipo 's26 ultra',
    'iphone 17 pro max'), los mapea a SKUs via resolver de sinónimos y
    llama al comparador estructurado. Devuelve texto markdown con tabla y
    conclusión — el LLM no participa."""

    # Fragmentos que son líneas de producto pero cuya marca real difiere.
    # Ej: "iphone" → buscar marca="apple", no query="iphone" (que matchea audio).
    _ALIAS_MARCA: dict[str, str] = {
        "iphone": "apple",
        "ipad": "apple",
        "macbook": "apple",
        "galaxy": "samsung",
        "xperia": "sony",
        "moto": "motorola",
        "redmi": "xiaomi",
        "poco": "xiaomi",
        "honor": "huawei",
    }

    def __init__(
        self,
        resolver: ResolverCategoriaSinonimoHandler,
        comparar: CompararProductosHandler,
        buscar: BuscarProductosHandler | None = None,
    ) -> None:
        self._resolver = resolver
        self._comparar = comparar
        self._buscar = buscar

    def responder(
        self, intent: ComparacionExplicita
    ) -> RespuestaComparacionExplicita | None:
        skus = self._fragmentos_a_skus(intent.fragmentos)
        return self.responder_por_skus(skus)

    def responder_por_skus(
        self, skus: list[str]
    ) -> RespuestaComparacionExplicita | None:
        """Variante usada por otros short-circuits que ya tienen SKUs (ej.
        'ayudame a decidir' sobre los productos mostrados del turno anterior)."""
        if len(skus) < 2:
            return None
        resultado = self._comparar.ejecutar(CompararProductosQuery(skus=tuple(skus)))
        if resultado.tabla is None or len(resultado.productos) < 2:
            return None
        return RespuestaComparacionExplicita(
            texto=self._formatear(resultado),
            resultado=resultado,
        )

    def _fragmentos_a_skus(self, fragmentos: list[str]) -> list[str]:
        """Cada fragmento pasa por el resolver; si tiene sku_especifico lo usa
        directamente. Si no, busca por marca o texto según el tipo de fragmento.

        Reglas de búsqueda en cascade:
        1. Resolver sinónimo → sku_especifico directo.
        2. Si el fragmento es un alias de marca (iphone→apple, galaxy→samsung),
           busca con marca= para no matchear productos random por fulltext.
        3. Si no, fulltext query= con categoria_inferida del primer resultado.
        La categoría del primer producto encontrado se aplica a todos los
        siguientes para mantener coherencia (ej: iPhone en celulares → Samsung
        en celulares, no Samsung en TV)."""
        skus: list[str] = []
        vistos: set[str] = set()
        categoria_inferida: str | None = None
        for frag in fragmentos:
            res = self._resolver.ejecutar(
                ResolverCategoriaSinonimoQuery(texto=frag, limite_relaciones=0)
            )
            sin = res.sinonimo_directo
            sku = sin.sku_especifico if sin else None
            # Propagar categoría del resolver aunque no haya sku_especifico
            # (ej: "samsung galaxy" → Celulares sin SKU específico).
            if sin and sin.categoria and categoria_inferida is None:
                categoria_inferida = sin.categoria
            if not sku and self._buscar:
                frag_lower = frag.lower().strip()
                marca_alias = self._ALIAS_MARCA.get(frag_lower)
                # Si no es alias exacto, comprueba si el fragmento completo
                # es solo el nombre de una marca conocida (ej. "samsung").
                if not marca_alias:
                    from .detector_marca_mensaje import DetectorMarcaMensaje
                    m = DetectorMarcaMensaje.extraer(frag)
                    # Solo usa búsqueda por marca cuando el fragmento ES la
                    # marca (<=2 tokens) para no perder modelo en "samsung A55".
                    if m and len(frag_lower.split()) <= 2:
                        marca_alias = m
                if marca_alias:
                    resultados = self._buscar.ejecutar(
                        BuscarProductosQuery(
                            marca=marca_alias,
                            categoria=categoria_inferida,
                            limite=1,
                            excluir_accesorios=True,
                        )
                    )
                else:
                    resultados = self._buscar.ejecutar(
                        BuscarProductosQuery(
                            query=frag,
                            categoria=categoria_inferida,
                            limite=1,
                            excluir_accesorios=True,
                        )
                    )
                if resultados:
                    sku = str(resultados[0].sku)
                    if categoria_inferida is None:
                        categoria_inferida = resultados[0].categoria
            if sku and sku not in vistos:
                vistos.add(sku)
                skus.append(sku)
        return skus

    @staticmethod
    def _formatear(r: ResultadoCompararProductos) -> str:
        return RenderizadorTablaComparacion.render(
            tabla=r.tabla,
            conclusion=r.conclusion,
            productos_por_sku={str(p.sku): p for p in r.productos},
        )

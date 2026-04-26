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
        directamente. Si no, busca en el catálogo por texto para encontrar el
        producto más relevante — permite comparar 'galaxy s25' con 'iphone 16'
        aunque no estén mapeados como aliases con SKU específico."""
        skus: list[str] = []
        vistos: set[str] = set()
        for frag in fragmentos:
            res = self._resolver.ejecutar(
                ResolverCategoriaSinonimoQuery(texto=frag, limite_relaciones=0)
            )
            sin = res.sinonimo_directo
            sku = sin.sku_especifico if sin else None
            if not sku and self._buscar:
                resultados = self._buscar.ejecutar(
                    BuscarProductosQuery(query=frag, limite=1, excluir_accesorios=True)
                )
                sku = str(resultados[0].sku) if resultados else None
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

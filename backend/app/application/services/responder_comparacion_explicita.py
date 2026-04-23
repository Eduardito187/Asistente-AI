from __future__ import annotations

from dataclasses import dataclass

from ..queries.comparar_productos import CompararProductosHandler, CompararProductosQuery
from ..queries.comparar_productos.result import ResultadoCompararProductos
from ..queries.resolver_categoria_sinonimo import (
    ResolverCategoriaSinonimoHandler,
    ResolverCategoriaSinonimoQuery,
)
from .detector_comparacion_explicita import ComparacionExplicita


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
    ) -> None:
        self._resolver = resolver
        self._comparar = comparar

    def responder(
        self, intent: ComparacionExplicita
    ) -> RespuestaComparacionExplicita | None:
        skus = self._fragmentos_a_skus(intent.fragmentos)
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
        """Cada fragmento pasa por el resolver; nos quedamos solo con los
        que resolvieron a un SKU concreto (alias → sku_especifico)."""
        skus: list[str] = []
        vistos: set[str] = set()
        for frag in fragmentos:
            res = self._resolver.ejecutar(
                ResolverCategoriaSinonimoQuery(texto=frag, limite_relaciones=0)
            )
            sin = res.sinonimo_directo
            sku = sin.sku_especifico if sin else None
            if sku and sku not in vistos:
                vistos.add(sku)
                skus.append(sku)
        return skus

    @staticmethod
    def _formatear(r: ResultadoCompararProductos) -> str:
        tabla = r.tabla or {}
        conclusion = r.conclusion or {}
        nombres = tabla.get("nombres", [])
        filas = tabla.get("filas", [])
        lineas = ["Te comparo los que mencionaste:\n"]
        # Encabezado: Atributo | Nombre1 | Nombre2 | ...
        encabezado = ["**Atributo**", *(f"**{n}**" for n in nombres)]
        lineas.append("| " + " | ".join(encabezado) + " |")
        lineas.append("| " + " | ".join(["---"] * (len(nombres) + 1)) + " |")
        for fila in filas:
            campo = fila.get("campo", "")
            valores = [str(v) for v in fila.get("valores", [])]
            lineas.append(f"| {campo} | " + " | ".join(valores) + " |")
        # Bullets de conclusión, cada uno con SKU para que la UI renderice tarjetas.
        por_sku = {str(p.sku): p for p in r.productos}
        lineas.append("")
        for clave, etiqueta in (
            ("mejor_general", "Mejor opción general"),
            ("mejor_precio_calidad", "Mejor relación precio/calidad"),
            ("mas_economica", "Opción más económica"),
        ):
            bloque = conclusion.get(clave) or {}
            sku = bloque.get("sku")
            razon = bloque.get("razon", "")
            prod = por_sku.get(sku)
            if prod is not None:
                lineas.append(f"- **{etiqueta}:** {prod.nombre} [{sku}] — {razon}")
        return "\n".join(lineas)

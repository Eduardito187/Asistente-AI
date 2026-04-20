from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..queries.resolver_categoria_sinonimo import (
    ResolverCategoriaSinonimoHandler,
    ResolverCategoriaSinonimoQuery,
)


@dataclass(frozen=True)
class CategoriaCercana:
    """Resultado de la resolucion: la categoria real con la que vamos a
    intentar buscar alternativas + la razon humana para explicarle al cliente
    por que le estamos ofreciendo esto y no lo que pidio."""

    categoria: str
    subcategoria: Optional[str]
    razon: Optional[str]
    fuente: str
    palabra_clave: Optional[str] = None
    marca: Optional[str] = None


class ResolvedorCategoriaCercana:
    """SRP: traducir el texto libre del cliente a una categoria real del
    catalogo ANTES de llamar al LLM o de negar la existencia.

    Fuente estructurada de verdad: BD (categorias_sinonimos + categorias_relacionadas).
    El LLM no se usa aqui — esta clase es deterministica y explica con 'razon'
    por que elegimos esa categoria."""

    def __init__(self, resolver: ResolverCategoriaSinonimoHandler) -> None:
        self._resolver = resolver

    def resolver(self, texto_cliente: str) -> Optional[CategoriaCercana]:
        if not texto_cliente:
            return None
        resultado = self._resolver.ejecutar(
            ResolverCategoriaSinonimoQuery(texto=texto_cliente)
        )
        sinonimo = resultado.sinonimo_directo
        if sinonimo is not None:
            return CategoriaCercana(
                categoria=sinonimo.categoria,
                subcategoria=sinonimo.subcategoria,
                razon=None,
                fuente="sinonimo",
                palabra_clave=sinonimo.palabra_clave,
            )
        relacionada = resultado.mejor_relacionada
        if relacionada is not None:
            return CategoriaCercana(
                categoria=relacionada.categoria_sugerida,
                subcategoria=relacionada.subcategoria_sugerida,
                razon=relacionada.razon,
                fuente="relacionada",
                marca=relacionada.categoria_origen,
            )
        return None

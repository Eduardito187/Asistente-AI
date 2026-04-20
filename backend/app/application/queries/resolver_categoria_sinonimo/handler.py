from __future__ import annotations

from difflib import SequenceMatcher
from typing import Callable

from ....domain.catalogo import CategoriaSinonimo
from ....domain.shared.normalizacion import NormalizadorTexto
from ....domain.shared.tokens_consulta import TokensConsulta
from ...ports import UnitOfWork
from .query import ResolverCategoriaSinonimoQuery
from .result import ResolverCategoriaSinonimoResult


class ResolverCategoriaSinonimoHandler:
    """Handler CQRS: resolver texto del cliente → categoria real o relacionada.

    Estrategia:
      1. Normalizar el texto + tokenizar.
      2. Intentar match exacto por frase completa normalizada.
      3. Si falla, buscar por tokens (la palabra con mayor confianza gana).
      4. Si tampoco hay token match, fuzzy por prefijo+longitud (tolera typos
         como 'laptp' → 'laptop').
      5. Independiente del match, buscar relaciones cruzadas por el termino
         original (asi 'tesla' sigue devolviendo motocicletas aunque tesla
         este como sinonimo)."""

    _FUZZY_RATIO_MIN = 0.78

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(
        self, q: ResolverCategoriaSinonimoQuery
    ) -> ResolverCategoriaSinonimoResult:
        texto_norm = NormalizadorTexto.normalizar(q.texto)
        tokens = [t for t in TokensConsulta.significativos(texto_norm) if len(t) >= 3]

        with self._uow_factory() as uow:
            sinonimo = uow.catalogo_keywords.buscar_sinonimo_exacto(texto_norm)
            if sinonimo is None and tokens:
                candidatos = uow.catalogo_keywords.buscar_sinonimos_por_tokens(
                    tokens, limite=5
                )
                sinonimo = candidatos[0] if candidatos else None
            if sinonimo is None and tokens:
                sinonimo = self._match_fuzzy(uow, tokens)

            relacionadas = self._buscar_relacionadas(uow, q.texto, tokens, q.limite_relaciones)

        return ResolverCategoriaSinonimoResult(
            termino_original=q.texto.strip(),
            sinonimo_directo=sinonimo,
            relacionadas=relacionadas,
        )

    @classmethod
    def _match_fuzzy(cls, uow, tokens: list[str]) -> CategoriaSinonimo | None:
        """Tolera typos leves cuando no hubo match exacto ni por token:
        prefiltra por prefijo+longitud en BD y elige el sinonimo con mayor
        ratio de similitud (>= _FUZZY_RATIO_MIN)."""
        mejor: tuple[float, CategoriaSinonimo] | None = None
        for token in tokens:
            if len(token) < 4:
                continue
            for cand in uow.catalogo_keywords.buscar_sinonimos_fuzzy(token, limite=10):
                ratio = SequenceMatcher(None, token, cand.palabra_clave_norm).ratio()
                if ratio < cls._FUZZY_RATIO_MIN:
                    continue
                score = ratio * float(cand.confianza or 1.0)
                if mejor is None or score > mejor[0]:
                    mejor = (score, cand)
        return mejor[1] if mejor else None

    @staticmethod
    def _buscar_relacionadas(uow, texto_original: str, tokens: list[str], limite: int):
        candidatos = [texto_original.strip().lower(), *tokens]
        vistos: set[tuple[str, str]] = set()
        resultado = []
        for termino in candidatos:
            if not termino:
                continue
            for r in uow.catalogo_keywords.buscar_relacionadas(termino, limite=limite):
                clave = (r.categoria_sugerida, r.subcategoria_sugerida or "")
                if clave in vistos:
                    continue
                vistos.add(clave)
                resultado.append(r)
                if len(resultado) >= limite:
                    return resultado
        return resultado

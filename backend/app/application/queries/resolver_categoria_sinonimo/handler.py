from __future__ import annotations

import json
from dataclasses import asdict
from difflib import SequenceMatcher
from typing import Callable, Optional

from ....domain.catalogo import CategoriaRelacionada, CategoriaSinonimo
from ....domain.shared.normalizacion import NormalizadorTexto
from ....domain.shared.normalizador_fonetico import NormalizadorFonetico
from ....domain.shared.tokens_consulta import TokensConsulta
from ...ports import Cache, UnitOfWork
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
    _CACHE_TTL_S = 600

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        cache: Optional[Cache] = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._cache = cache

    def ejecutar(
        self, q: ResolverCategoriaSinonimoQuery
    ) -> ResolverCategoriaSinonimoResult:
        texto_norm = NormalizadorTexto.normalizar(q.texto)
        cache_key = f"sin:{q.limite_relaciones}:{texto_norm}"
        cached = self._cache_get(cache_key, texto_original=q.texto.strip())
        if cached is not None:
            return cached

        tokens = [t for t in TokensConsulta.significativos(texto_norm) if len(t) >= 3]

        with self._uow_factory() as uow:
            sinonimo = uow.catalogo_keywords.buscar_sinonimo_exacto(texto_norm)
            if sinonimo is None:
                sinonimo = self._match_ngrama(uow, texto_norm)
            if sinonimo is None and tokens:
                candidatos = uow.catalogo_keywords.buscar_sinonimos_por_tokens(
                    tokens, limite=5
                )
                sinonimo = candidatos[0] if candidatos else None
            if sinonimo is None and tokens:
                sinonimo = self._match_fuzzy(uow, tokens)

            relacionadas = self._buscar_relacionadas(uow, q.texto, tokens, q.limite_relaciones)

        resultado = ResolverCategoriaSinonimoResult(
            termino_original=q.texto.strip(),
            sinonimo_directo=sinonimo,
            relacionadas=relacionadas,
        )
        self._cache_set(cache_key, resultado)
        return resultado

    def _cache_get(
        self, key: str, *, texto_original: str
    ) -> Optional[ResolverCategoriaSinonimoResult]:
        if self._cache is None:
            return None
        raw = self._cache.get(key)
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            return None
        sin = data.get("sinonimo_directo")
        sinonimo = CategoriaSinonimo(**sin) if sin else None
        relacionadas = [CategoriaRelacionada(**r) for r in data.get("relacionadas", [])]
        return ResolverCategoriaSinonimoResult(
            termino_original=texto_original,
            sinonimo_directo=sinonimo,
            relacionadas=relacionadas,
        )

    def _cache_set(self, key: str, resultado: ResolverCategoriaSinonimoResult) -> None:
        if self._cache is None:
            return
        payload = {
            "sinonimo_directo": asdict(resultado.sinonimo_directo) if resultado.sinonimo_directo else None,
            "relacionadas": [asdict(r) for r in resultado.relacionadas],
        }
        self._cache.set(key, json.dumps(payload), ttl_segundos=self._CACHE_TTL_S)

    @staticmethod
    def _match_ngrama(uow, texto_norm: str) -> CategoriaSinonimo | None:
        """Busca la frase sinonimo mas larga contenida en el texto.

        Ejemplo: en 'quiero un smart watch' prueba trigramas ('un smart watch',
        'quiero un smart') y bigramas ('smart watch', 'un smart', 'quiero un')
        hasta encontrar match exacto en categorias_sinonimos. Asi 'smart watch'
        se detecta aunque el cliente lo diga dentro de una oracion."""
        palabras = texto_norm.split()
        if len(palabras) < 2:
            return None
        for tamanio in (3, 2):
            for i in range(len(palabras) - tamanio + 1):
                frase = " ".join(palabras[i : i + tamanio])
                match = uow.catalogo_keywords.buscar_sinonimo_exacto(frase)
                if match is not None:
                    return match
        return None

    @classmethod
    def _match_fuzzy(cls, uow, tokens: list[str]) -> CategoriaSinonimo | None:
        """Tolera typos leves cuando no hubo match exacto ni por token:
        prefiltra por prefijo+longitud en BD y elige el sinonimo con mayor
        ratio de similitud (>= _FUZZY_RATIO_MIN).

        Ademas del ratio contra la forma normalizada, calcula el ratio contra
        la forma fonetica (colapsa b↔v, c↔s, h muda) — asi 'cosinas' matchea
        'cocinas', 'labadora' matchea 'lavadora', 'haire' matchea 'aire'."""
        mejor: tuple[float, CategoriaSinonimo] | None = None
        for token in tokens:
            if len(token) < 4:
                continue
            token_fon = NormalizadorFonetico.normalizar(token)
            # Buscamos por el token original Y por el fonetico para cubrir los
            # casos donde el prefijo de 2 chars cambia tras la normalizacion.
            candidatos = uow.catalogo_keywords.buscar_sinonimos_fuzzy(token, limite=30)
            if token_fon != token:
                candidatos = candidatos + uow.catalogo_keywords.buscar_sinonimos_fuzzy(token_fon, limite=30)
            vistos_sku = set()
            for cand in candidatos:
                clave = (cand.palabra_clave_norm, cand.categoria, cand.subcategoria)
                if clave in vistos_sku:
                    continue
                vistos_sku.add(clave)
                ratio_raw = SequenceMatcher(None, token, cand.palabra_clave_norm).ratio()
                ratio_fon = SequenceMatcher(
                    None, token_fon,
                    NormalizadorFonetico.normalizar(cand.palabra_clave_norm)
                ).ratio()
                ratio = max(ratio_raw, ratio_fon)
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

from __future__ import annotations

import logging
from typing import Callable

from ..ports import EmbedderPort, UnitOfWork
from .calculador_similitud import CalculadorSimilitud
from .codificador_vectorial import CodificadorVectorial

log = logging.getLogger("buscador_semantico")

UMBRAL_SIMILITUD = 0.55
TOP_K = 6


class BuscadorSemantico:
    """SRP: buscar SKUs por similitud coseno sobre los embeddings persistidos.

    Usa el Embedder para vectorizar el query del usuario, lee los embeddings
    desde el repo y rankea. No toca FULLTEXT — es complementario."""

    def __init__(self, embedder: EmbedderPort, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._embedder = embedder
        self._uow_factory = uow_factory
        self._cache_vectores: list[tuple[str, list[float]]] | None = None

    def buscar_skus(self, query: str, limite: int = TOP_K) -> list[str]:
        q = (query or "").strip()
        if not q:
            return []
        vectors = self._embedder.embed([q])
        if not vectors:
            return []
        consulta = vectors[0]
        candidatos = self._vectores_catalogo()
        if not candidatos:
            return []
        puntuados = [
            (sku, CalculadorSimilitud.coseno(consulta, vec))
            for sku, vec in candidatos
        ]
        puntuados.sort(key=lambda x: x[1], reverse=True)
        return [sku for sku, score in puntuados[:limite] if score >= UMBRAL_SIMILITUD]

    def invalidar_cache(self) -> None:
        self._cache_vectores = None

    def _vectores_catalogo(self) -> list[tuple[str, list[float]]]:
        if self._cache_vectores is not None:
            return self._cache_vectores
        try:
            with self._uow_factory() as uow:
                embeddings = uow.productos_embeddings.listar_todos()
        except Exception as exc:
            log.warning("no se pudieron leer embeddings: %s", exc)
            return []
        self._cache_vectores = [
            (e.sku, CodificadorVectorial.desde_bytes(e.vector)) for e in embeddings
        ]
        return self._cache_vectores

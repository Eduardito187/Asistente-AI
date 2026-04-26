from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .categoria_relacionada import CategoriaRelacionada
from .categoria_sinonimo import CategoriaSinonimo


class CatalogoKeywordsRepository(ABC):
    """Puerto de persistencia del vocabulario del catalogo. La implementacion
    vive en infrastructure/persistence."""

    @abstractmethod
    def buscar_sinonimo_exacto(
        self, palabra_norm: str
    ) -> Optional[CategoriaSinonimo]: ...

    @abstractmethod
    def buscar_sinonimos_por_tokens(
        self, tokens_norm: list[str], limite: int = 5
    ) -> list[CategoriaSinonimo]: ...

    @abstractmethod
    def buscar_sinonimos_por_primer_token(
        self, primer_token: str, limite: int = 30
    ) -> list[CategoriaSinonimo]: ...

    @abstractmethod
    def buscar_sinonimos_fuzzy(
        self, token_norm: str, limite: int = 10
    ) -> list[CategoriaSinonimo]: ...

    @abstractmethod
    def buscar_relacionadas(
        self, categoria_origen: str, limite: int = 5
    ) -> list[CategoriaRelacionada]: ...

    @abstractmethod
    def skus_por_keyword(
        self, keyword_norm: str, limite: int = 10
    ) -> list[str]: ...

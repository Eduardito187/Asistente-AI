from __future__ import annotations

from abc import ABC, abstractmethod


class EmbedderPort(ABC):
    """Puerto de salida: produce embeddings para textos (busqueda semantica)."""

    @abstractmethod
    def embed(self, textos: list[str]) -> list[list[float]]: ...

    @property
    @abstractmethod
    def modelo(self) -> str: ...

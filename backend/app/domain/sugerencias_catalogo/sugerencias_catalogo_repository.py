from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .sugerencia_catalogo import SugerenciaCatalogo


class SugerenciasCatalogoRepository(ABC):
    """Puerto de persistencia del agregado SugerenciaCatalogo."""

    @abstractmethod
    def por_nombre_norm(self, nombre_norm: str) -> Optional[SugerenciaCatalogo]: ...

    @abstractmethod
    def insertar(self, sugerencia: SugerenciaCatalogo) -> int: ...

    @abstractmethod
    def incrementar(self, nombre_norm: str) -> None: ...

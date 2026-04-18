from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from .sesion import Sesion


class SesionRepository(ABC):
    """Puerto de persistencia del agregado Sesion."""

    @abstractmethod
    def crear(self, sesion: Sesion) -> None: ...

    @abstractmethod
    def obtener(self, sesion_id: UUID) -> Optional[Sesion]: ...

    @abstractmethod
    def existe(self, sesion_id: UUID) -> bool: ...

    @abstractmethod
    def guardar(self, sesion: Sesion) -> None: ...

    @abstractmethod
    def tocar(self, sesion_id: UUID) -> None: ...

    @abstractmethod
    def marcar_abandonadas(self, umbral_horas: int) -> int: ...

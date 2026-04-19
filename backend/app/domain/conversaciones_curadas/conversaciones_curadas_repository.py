from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .conversacion_curada import ConversacionCurada


class ConversacionesCuradasRepository(ABC):
    """Puerto de persistencia del agregado ConversacionCurada."""

    @abstractmethod
    def guardar(self, conv: ConversacionCurada) -> int: ...

    @abstractmethod
    def actualizar(self, conv: ConversacionCurada) -> None: ...

    @abstractmethod
    def por_sesion(self, sesion_id: UUID) -> ConversacionCurada | None: ...

    @abstractmethod
    def top_activas(self, limite: int) -> list[ConversacionCurada]: ...

    @abstractmethod
    def listar(self, limite: int, offset: int) -> list[ConversacionCurada]: ...

    @abstractmethod
    def set_activa(self, id_: int, activa: bool) -> None: ...

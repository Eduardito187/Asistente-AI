from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from .mensaje import Mensaje


class ChatRepository(ABC):
    """Puerto de persistencia para la conversación de chat."""

    @abstractmethod
    def guardar(self, mensaje: Mensaje) -> None: ...

    @abstractmethod
    def historial(self, sesion_id: UUID, limite: int) -> list[Mensaje]: ...

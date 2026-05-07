from __future__ import annotations

from abc import ABC, abstractmethod

from .conversacion_fallida import ConversacionFallida


class ConversacionesFallidasRepository(ABC):
    """Puerto de salida del agregado ConversacionFallida."""

    @abstractmethod
    def guardar(self, conv: ConversacionFallida) -> None: ...

    @abstractmethod
    def listar_recientes(self, limite: int = 50) -> list[ConversacionFallida]: ...

    @abstractmethod
    def contar_por_razon(self) -> dict[str, int]: ...

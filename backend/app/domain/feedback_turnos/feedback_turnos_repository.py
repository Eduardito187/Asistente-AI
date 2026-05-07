from __future__ import annotations

from abc import ABC, abstractmethod

from .feedback_turno import FeedbackTurno


class FeedbackTurnosRepository(ABC):
    """Puerto del agregado FeedbackTurno."""

    @abstractmethod
    def guardar(self, fb: FeedbackTurno) -> int: ...

    @abstractmethod
    def listar_negativos(self, limite: int = 50) -> list[FeedbackTurno]: ...

    @abstractmethod
    def listar_positivos(self, limite: int = 50) -> list[FeedbackTurno]: ...

    @abstractmethod
    def stats(self) -> dict: ...

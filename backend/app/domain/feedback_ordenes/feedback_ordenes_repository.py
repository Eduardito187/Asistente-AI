from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from .feedback_orden import FeedbackOrden


class FeedbackOrdenesRepository(ABC):
    """Puerto de persistencia del agregado FeedbackOrden."""

    @abstractmethod
    def registrar(self, feedback: FeedbackOrden) -> int: ...

    @abstractmethod
    def obtener_por_orden(self, orden_id: UUID) -> Optional[FeedbackOrden]: ...

    @abstractmethod
    def ultima_orden_sin_feedback(self, sesion_id: UUID) -> Optional[UUID]: ...

    @abstractmethod
    def listar_recientes(self, limite: int) -> list[FeedbackOrden]: ...

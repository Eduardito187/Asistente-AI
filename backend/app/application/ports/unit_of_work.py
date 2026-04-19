from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...domain.carritos import CarritoRepository
    from ...domain.chat import ChatRepository
    from ...domain.conversaciones_curadas import ConversacionesCuradasRepository
    from ...domain.feedback_ordenes import FeedbackOrdenesRepository
    from ...domain.metricas_turno import MetricasTurnoRepository
    from ...domain.ordenes import OrdenRepository
    from ...domain.perfiles_sesion import PerfilSesionRepository
    from ...domain.productos import ProductoRepository
    from ...domain.productos_embeddings import ProductosEmbeddingsRepository
    from ...domain.sesiones import SesionRepository
    from ...domain.sugerencias_catalogo import SugerenciasCatalogoRepository


class UnitOfWork(ABC):
    """Agrupa repositorios y delimita la transaccion. SRP: manejar el boundary."""

    productos: "ProductoRepository"
    sesiones: "SesionRepository"
    carritos: "CarritoRepository"
    ordenes: "OrdenRepository"
    chat: "ChatRepository"
    sugerencias_catalogo: "SugerenciasCatalogoRepository"
    conversaciones_curadas: "ConversacionesCuradasRepository"
    metricas_turno: "MetricasTurnoRepository"
    perfiles_sesion: "PerfilSesionRepository"
    feedback_ordenes: "FeedbackOrdenesRepository"
    productos_embeddings: "ProductosEmbeddingsRepository"

    @abstractmethod
    def __enter__(self) -> "UnitOfWork": ...

    @abstractmethod
    def __exit__(self, exc_type, exc, tb) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

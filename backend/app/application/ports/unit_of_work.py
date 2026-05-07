from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...domain.carritos import CarritoRepository
    from ...domain.catalogo import CatalogoKeywordsRepository
    from ...domain.chat import ChatRepository
    from ...domain.conversaciones_curadas import ConversacionesCuradasRepository
    from ...domain.conversaciones_fallidas import ConversacionesFallidasRepository
    from ...domain.feedback_ordenes import FeedbackOrdenesRepository
    from ...domain.feedback_turnos import FeedbackTurnosRepository
    from ...domain.golden_conversations import GoldenConversationsRepository
    from ...domain.negative_patterns import NegativePatternsRepository
    from ...domain.metricas_turno import MetricasTurnoRepository
    from ...domain.ordenes import OrdenRepository
    from ...domain.perfiles_historicos import PerfilesHistoricosRepository
    from ...domain.perfiles_sesion import PerfilSesionRepository
    from ...domain.synonyms_candidatos import SynonymsCandidatosRepository
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
    catalogo_keywords: "CatalogoKeywordsRepository"
    conversaciones_fallidas: "ConversacionesFallidasRepository"
    synonyms_candidatos: "SynonymsCandidatosRepository"
    perfiles_historicos: "PerfilesHistoricosRepository"
    feedback_turnos: "FeedbackTurnosRepository"
    golden_conversations: "GoldenConversationsRepository"
    negative_patterns: "NegativePatternsRepository"

    @abstractmethod
    def __enter__(self) -> "UnitOfWork": ...

    @abstractmethod
    def __exit__(self, exc_type, exc, tb) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

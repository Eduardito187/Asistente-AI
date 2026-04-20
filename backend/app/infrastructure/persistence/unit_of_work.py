from __future__ import annotations

from sqlalchemy.orm import Session

from ...application.ports import UnitOfWork
from .engine import SessionLocal
from .mariadb.carrito_repositorio import MariaDbCarritoRepository
from .mariadb.catalogo_keywords_repositorio import MariaDbCatalogoKeywordsRepository
from .mariadb.chat_repositorio import MariaDbChatRepository
from .mariadb.conversaciones_curadas_repositorio import MariaDbConversacionesCuradasRepository
from .mariadb.feedback_ordenes_repositorio import MariaDbFeedbackOrdenesRepository
from .mariadb.metricas_turno_repositorio import MariaDbMetricasTurnoRepository
from .mariadb.orden_repositorio import MariaDbOrdenRepository
from .mariadb.perfil_sesion_repositorio import MariaDbPerfilSesionRepository
from .mariadb.producto_repositorio import MariaDbProductoRepository
from .mariadb.productos_embeddings_repositorio import MariaDbProductosEmbeddingsRepository
from .mariadb.sesion_repositorio import MariaDbSesionRepository
from .mariadb.sugerencias_catalogo_repositorio import MariaDbSugerenciasCatalogoRepository


class SqlAlchemyUnitOfWork(UnitOfWork):
    """SRP: manejar el boundary transaccional de SQLAlchemy."""

    def __init__(self) -> None:
        self._session: Session | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = SessionLocal()
        self.productos = MariaDbProductoRepository(self._session)
        self.sesiones = MariaDbSesionRepository(self._session)
        self.carritos = MariaDbCarritoRepository(self._session)
        self.ordenes = MariaDbOrdenRepository(self._session)
        self.chat = MariaDbChatRepository(self._session)
        self.sugerencias_catalogo = MariaDbSugerenciasCatalogoRepository(self._session)
        self.conversaciones_curadas = MariaDbConversacionesCuradasRepository(self._session)
        self.metricas_turno = MariaDbMetricasTurnoRepository(self._session)
        self.perfiles_sesion = MariaDbPerfilSesionRepository(self._session)
        self.feedback_ordenes = MariaDbFeedbackOrdenesRepository(self._session)
        self.productos_embeddings = MariaDbProductosEmbeddingsRepository(self._session)
        self.catalogo_keywords = MariaDbCatalogoKeywordsRepository(self._session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is not None:
                self.rollback()
        finally:
            if self._session is not None:
                self._session.close()
                self._session = None

    def commit(self) -> None:
        assert self._session is not None
        self._session.commit()

    def rollback(self) -> None:
        assert self._session is not None
        self._session.rollback()

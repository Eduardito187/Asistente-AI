from __future__ import annotations

from sqlalchemy.orm import Session

from ...application.ports import UnitOfWork
from .engine import SessionLocal
from .mariadb.carrito_repositorio import MariaDbCarritoRepository
from .mariadb.chat_repositorio import MariaDbChatRepository
from .mariadb.orden_repositorio import MariaDbOrdenRepository
from .mariadb.producto_repositorio import MariaDbProductoRepository
from .mariadb.sesion_repositorio import MariaDbSesionRepository


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

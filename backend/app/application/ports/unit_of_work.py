from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...domain.carritos import CarritoRepository
    from ...domain.chat import ChatRepository
    from ...domain.ordenes import OrdenRepository
    from ...domain.productos import ProductoRepository
    from ...domain.sesiones import SesionRepository


class UnitOfWork(ABC):
    """Agrupa repositorios y delimita la transaccion. SRP: manejar el boundary."""

    productos: "ProductoRepository"
    sesiones: "SesionRepository"
    carritos: "CarritoRepository"
    ordenes: "OrdenRepository"
    chat: "ChatRepository"

    @abstractmethod
    def __enter__(self) -> "UnitOfWork": ...

    @abstractmethod
    def __exit__(self, exc_type, exc, tb) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from ..productos import SKU
from .carrito import Carrito


class CarritoRepository(ABC):
    """Puerto de persistencia del agregado Carrito."""

    @abstractmethod
    def obtener(self, sesion_id: UUID) -> Carrito: ...

    @abstractmethod
    def agregar_o_incrementar(self, sesion_id: UUID, sku: SKU, cantidad: int) -> None: ...

    @abstractmethod
    def quitar(self, sesion_id: UUID, sku: SKU) -> bool: ...

    @abstractmethod
    def vaciar(self, sesion_id: UUID) -> None: ...

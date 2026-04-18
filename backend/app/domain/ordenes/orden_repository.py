from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from .orden import Orden


class OrdenRepository(ABC):
    """Puerto de persistencia del agregado Orden."""

    @abstractmethod
    def persistir(self, orden: Orden) -> Orden:
        """Persiste la orden y retorna la instancia con numero_orden y created_at rellenados."""

    @abstractmethod
    def obtener_por_numero(self, numero_orden: str) -> Optional[Orden]: ...

    @abstractmethod
    def listar_por_sesion(self, sesion_id: UUID) -> List[Orden]: ...

    @abstractmethod
    def listar(self, limite: int = 50) -> List[Orden]: ...

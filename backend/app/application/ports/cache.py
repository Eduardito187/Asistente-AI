from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class Cache(ABC):
    """Puerto de cache clave-valor con TTL. La implementacion real (Redis)
    vive en infrastructure/cache. Un adaptador NoOp permite correr sin cache
    en desarrollo o cuando Redis no esta disponible."""

    @abstractmethod
    def get(self, key: str) -> Optional[str]: ...

    @abstractmethod
    def set(self, key: str, value: str, ttl_segundos: int) -> None: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

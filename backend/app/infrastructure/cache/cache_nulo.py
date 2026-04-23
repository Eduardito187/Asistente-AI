from __future__ import annotations

from typing import Optional

from ...application.ports import Cache


class CacheNulo(Cache):
    """Fallback cuando no hay Redis disponible: no-op silencioso.

    Permite que los handlers llamen a cache sin tener que chequear
    `if cache is None` en cada sitio. Ideal para dev, tests o cuando
    el cluster de cache esta temporalmente caido."""

    def get(self, key: str) -> Optional[str]:
        return None

    def set(self, key: str, value: str, ttl_segundos: int) -> None:
        return None

    def delete(self, key: str) -> None:
        return None

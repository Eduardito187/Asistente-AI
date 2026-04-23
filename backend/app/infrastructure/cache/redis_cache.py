from __future__ import annotations

import logging
from typing import Optional

import redis

from ...application.ports import Cache

log = logging.getLogger("cache")


class RedisCache(Cache):
    """Adaptador de cache contra Redis. Falla de forma silenciosa: si Redis
    no responde, los handlers siguen funcionando (peor latencia, no error)."""

    def __init__(self, url: str) -> None:
        self._client: redis.Redis = redis.Redis.from_url(
            url, socket_timeout=0.5, socket_connect_timeout=0.5, decode_responses=True
        )

    def get(self, key: str) -> Optional[str]:
        try:
            return self._client.get(key)
        except redis.RedisError:
            log.warning("cache get fallo para %s — devolviendo miss", key)
            return None

    def set(self, key: str, value: str, ttl_segundos: int) -> None:
        try:
            self._client.set(key, value, ex=max(1, ttl_segundos))
        except redis.RedisError:
            log.warning("cache set fallo para %s — ignorado", key)

    def delete(self, key: str) -> None:
        try:
            self._client.delete(key)
        except redis.RedisError:
            log.warning("cache delete fallo para %s — ignorado", key)

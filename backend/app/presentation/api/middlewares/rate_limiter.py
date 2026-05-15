from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import HTTPException


class SessionRateLimiter:
    """Rate limiter por sesión_id. Límite: max_requests por ventana_segundos.

    En memoria (no Redis) — se pierde al reiniciar, suficiente para evitar
    spam. Para producción multi-instancia usar Redis como backend."""

    def __init__(self, max_requests: int = 60, ventana_segundos: float = 60.0) -> None:
        self._max = max_requests
        self._ventana = ventana_segundos
        self._ventanas: dict[str, Deque[float]] = defaultdict(deque)

    def verificar(self, sesion_id: str) -> None:
        """Lanza HTTPException 429 si la sesión excede el límite."""
        ahora = time.monotonic()
        cola = self._ventanas[sesion_id]
        # Purgar timestamps fuera de la ventana
        while cola and ahora - cola[0] > self._ventana:
            cola.popleft()
        if len(cola) >= self._max:
            raise HTTPException(
                status_code=429,
                detail=f"Demasiados mensajes. Espera {int(self._ventana)}s antes de continuar.",
            )
        cola.append(ahora)

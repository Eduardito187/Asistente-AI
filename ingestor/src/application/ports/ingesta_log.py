from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class IngestaLog(ABC):
    """Puerto de bitácora para trackear ejecuciones de ingesta."""

    @abstractmethod
    def iniciar(self, origen: str) -> int:
        """Registra el inicio de una ingesta y retorna su id."""

    @abstractmethod
    def completar(self, log_id: int, procesados: int) -> None: ...

    @abstractmethod
    def fallar(self, log_id: int, error: str) -> None: ...

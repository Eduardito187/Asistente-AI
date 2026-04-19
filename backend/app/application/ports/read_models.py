from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class CarritoReadModel(ABC):
    """Lectura pura contra vista_carritos (CQRS query-side)."""

    @abstractmethod
    def listar(
        self,
        estado: Optional[str],
        solo_con_items: bool,
        limite: int,
    ) -> list[dict]: ...


class DashboardMetricasReadModel(ABC):
    """Lectura agregada de metricas_turno para dashboards."""

    @abstractmethod
    def resumen_global(self, dias: int) -> dict: ...

    @abstractmethod
    def por_ruta(self, dias: int) -> list[dict]: ...

    @abstractmethod
    def latencias_ordenadas(self, dias: int) -> list[int]: ...

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardMetricasQuery:
    """Query: resumen operativo + percentiles de latencia + desglose por ruta."""

    dias: int = 7

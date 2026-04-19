from __future__ import annotations

from ...ports import DashboardMetricasReadModel
from .calculador_percentiles import CalculadorPercentiles
from .query import DashboardMetricasQuery
from .result import ResultadoDashboardMetricas


class DashboardMetricasHandler:
    """Handler CQRS: agrega numeros de metricas_turno para dashboard."""

    def __init__(self, read_model: DashboardMetricasReadModel) -> None:
        self._rm = read_model

    def ejecutar(self, q: DashboardMetricasQuery) -> ResultadoDashboardMetricas:
        resumen = self._rm.resumen_global(q.dias)
        por_ruta = self._rm.por_ruta(q.dias)
        latencias = self._rm.latencias_ordenadas(q.dias)
        turnos = int(resumen.get("turnos") or 0)
        sesiones = int(resumen.get("sesiones") or 0)
        cerradas = int(resumen.get("sesiones_con_orden") or 0)
        mentiras = int(resumen.get("turnos_con_mentiras") or 0)
        return ResultadoDashboardMetricas(
            dias=q.dias,
            turnos=turnos,
            sesiones=sesiones,
            sesiones_con_orden=cerradas,
            pct_sesiones_cerraron=self._pct(cerradas, sesiones),
            pct_turnos_con_mentiras=self._pct(mentiras, turnos),
            avg_ms=float(resumen.get("avg_ms") or 0),
            p50_ms=CalculadorPercentiles.p(latencias, 50),
            p95_ms=CalculadorPercentiles.p(latencias, 95),
            por_ruta=[
                {
                    "ruta": r.get("ruta"),
                    "turnos": int(r.get("turnos") or 0),
                    "avg_ms": float(r.get("avg_ms") or 0),
                }
                for r in por_ruta
            ],
        )

    @staticmethod
    def _pct(num: int, den: int) -> float:
        return round((num / den) * 100, 2) if den else 0.0

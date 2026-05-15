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
        top_cats = self._rm.top_categorias(q.dias)
        top_cities = self._rm.top_ciudades(q.dias)
        sin_res = self._rm.tasa_sin_resultado(q.dias)
        derivacion = self._rm.tasa_derivacion(q.dias)
        turnos = int(resumen.get("turnos") or 0)
        sesiones = int(resumen.get("sesiones") or 0)
        cerradas = int(resumen.get("sesiones_con_orden") or 0)
        mentiras = int(resumen.get("turnos_con_mentiras") or 0)
        pct_sin_res = float(sin_res.get("pct_sin_resultado") or 0)
        pct_der = float(derivacion.get("pct_derivacion") or 0)
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
            top_categorias=top_cats,
            top_ciudades=top_cities,
            pct_sin_resultado=pct_sin_res,
            pct_derivacion=pct_der,
            alerta_sin_resultado=pct_sin_res > 30.0,
            alerta_derivacion=pct_der > 15.0,
        )

    @staticmethod
    def _pct(num: int, den: int) -> float:
        return round((num / den) * 100, 2) if den else 0.0

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ....application.queries.dashboard_metricas import (
    DashboardMetricasHandler,
    DashboardMetricasQuery,
)
from ..deps import dashboard_metricas_handler

router = APIRouter(prefix="/metricas", tags=["metricas"])


@router.get("/dashboard")
def dashboard(
    dias: int = Query(default=7, ge=1, le=90),
    handler: DashboardMetricasHandler = Depends(dashboard_metricas_handler),
):
    r = handler.ejecutar(DashboardMetricasQuery(dias=dias))
    return {
        "dias": r.dias,
        "turnos": r.turnos,
        "sesiones": r.sesiones,
        "sesiones_con_orden": r.sesiones_con_orden,
        "pct_sesiones_cerraron": r.pct_sesiones_cerraron,
        "pct_turnos_con_mentiras": r.pct_turnos_con_mentiras,
        "avg_ms": r.avg_ms,
        "p50_ms": r.p50_ms,
        "p95_ms": r.p95_ms,
        "por_ruta": r.por_ruta,
        "top_categorias": r.top_categorias,
        "top_ciudades": r.top_ciudades,
        "pct_sin_resultado": r.pct_sin_resultado,
        "pct_derivacion": r.pct_derivacion,
        "alerta_sin_resultado": r.alerta_sin_resultado,
        "alerta_derivacion": r.alerta_derivacion,
    }


@router.get("/alertas")
def alertas(
    dias: int = Query(default=1, ge=1, le=7),
    handler: DashboardMetricasHandler = Depends(dashboard_metricas_handler),
):
    """Devuelve alertas activas basadas en umbrales. Para monitoreo."""
    r = handler.ejecutar(DashboardMetricasQuery(dias=dias))
    alertas_activas = []
    if r.alerta_sin_resultado:
        alertas_activas.append({
            "tipo": "sin_resultado",
            "mensaje": f"Tasa de búsquedas sin resultado: {r.pct_sin_resultado:.1f}% (umbral: 30%)",
            "valor": r.pct_sin_resultado,
        })
    if r.alerta_derivacion:
        alertas_activas.append({
            "tipo": "derivacion_alta",
            "mensaje": f"Tasa de derivación a humano: {r.pct_derivacion:.1f}% (umbral: 15%)",
            "valor": r.pct_derivacion,
        })
    return {"alertas": alertas_activas, "ok": len(alertas_activas) == 0}

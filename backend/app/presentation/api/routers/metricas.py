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
    }

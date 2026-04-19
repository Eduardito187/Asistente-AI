from __future__ import annotations

from sqlalchemy import text

from ....application.ports.read_models import DashboardMetricasReadModel
from ..engine import SessionLocal
from .sql import DashboardMetricasSql


class MariaDbDashboardMetricasReadModel(DashboardMetricasReadModel):
    """Lectura agregada de metricas_turno para dashboards."""

    def resumen_global(self, dias: int) -> dict:
        with SessionLocal() as s:
            row = s.execute(text(DashboardMetricasSql.RESUMEN_GLOBAL), {"dias": int(dias)}).mappings().first()
            cerradas = s.execute(text(DashboardMetricasSql.SESIONES_QUE_CERRARON), {"dias": int(dias)}).scalar()
        base = dict(row) if row else {"turnos": 0, "avg_ms": 0, "turnos_con_mentiras": 0, "tool_calls": 0, "sesiones": 0}
        base["sesiones_con_orden"] = int(cerradas or 0)
        return base

    def por_ruta(self, dias: int) -> list[dict]:
        with SessionLocal() as s:
            rows = s.execute(text(DashboardMetricasSql.POR_RUTA), {"dias": int(dias)}).mappings().all()
        return [dict(r) for r in rows]

    def latencias_ordenadas(self, dias: int) -> list[int]:
        with SessionLocal() as s:
            rows = s.execute(text(DashboardMetricasSql.LATENCIAS), {"dias": int(dias)}).scalars().all()
        return [int(x) for x in rows]

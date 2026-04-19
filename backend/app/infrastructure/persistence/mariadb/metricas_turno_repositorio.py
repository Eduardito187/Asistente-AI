from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.metricas_turno import MetricaTurno, MetricasTurnoRepository
from .sql import MetricaTurnoSql


class MariaDbMetricasTurnoRepository(MetricasTurnoRepository):
    """Impl MariaDB del repo de MetricaTurno."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def registrar(self, metrica: MetricaTurno) -> int:
        res = self._s.execute(
            text(MetricaTurnoSql.REGISTRAR),
            {
                "sesion_id": str(metrica.sesion_id),
                "mlen": int(metrica.mensaje_usuario_len),
                "rlen": int(metrica.respuesta_len),
                "tools": int(metrica.tool_calls),
                "mentiras": int(metrica.mentiras_detectadas),
                "prods": int(metrica.productos_citados),
                "ruta": (metrica.ruta or "agente")[:40],
                "ms": int(metrica.tiempo_ms),
            },
        )
        return int(res.lastrowid or 0)

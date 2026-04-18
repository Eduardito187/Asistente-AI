from __future__ import annotations

from sqlalchemy import Engine, text

from ...application.ports import IngestaLog
from .sql import IngestaLogSql


class MariaDbIngestaLog(IngestaLog):

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def iniciar(self, origen: str) -> int:
        with self._engine.begin() as conn:
            res = conn.execute(text(IngestaLogSql.INICIAR), {"o": origen})
            return int(res.lastrowid)

    def completar(self, log_id: int, procesados: int) -> None:
        with self._engine.begin() as conn:
            conn.execute(text(IngestaLogSql.COMPLETAR), {"n": procesados, "id": log_id})

    def fallar(self, log_id: int, error: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(text(IngestaLogSql.FALLAR), {"e": error[:5000], "id": log_id})

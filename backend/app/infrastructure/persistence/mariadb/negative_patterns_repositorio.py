from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.negative_patterns import NegativePattern, NegativePatternsRepository
from .mappers.negative_pattern_mapper import NegativePatternMapper
from .sql.negative_patterns_sql import NegativePatternsSql


class MariaDbNegativePatternsRepository(NegativePatternsRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def upsert(self, np: NegativePattern) -> None:
        self._s.execute(
            text(NegativePatternsSql.UPSERT),
            {
                "patron": np.patron,
                "reason": np.reason_code,
                "desc": np.descripcion,
                "activo": 1 if np.activo else 0,
            },
        )

    def listar_activos(self) -> list[NegativePattern]:
        rows = self._s.execute(text(NegativePatternsSql.LISTAR_ACTIVOS)).mappings().all()
        return [NegativePatternMapper.from_row(dict(r)) for r in rows]

    def incrementar_ocurrencia(self, patron: str) -> None:
        self._s.execute(text(NegativePatternsSql.INCREMENTAR), {"patron": patron})

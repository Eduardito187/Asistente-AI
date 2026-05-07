from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.golden_conversations import (
    GoldenConversation,
    GoldenConversationsRepository,
)
from .mappers.golden_conversation_mapper import GoldenConversationMapper
from .sql.golden_conversations_sql import GoldenConversationsSql


class MariaDbGoldenConversationsRepository(GoldenConversationsRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def upsert(self, golden: GoldenConversation) -> int:
        result = self._s.execute(
            text(GoldenConversationsSql.UPSERT),
            {
                "caso": golden.caso_que_cubre,
                "cat": golden.categoria,
                "intencion": golden.intencion,
                "uso": golden.uso,
                "cliente": golden.cliente_texto[:1000],
                "asistente": golden.asistente_texto[:2000],
                "prio": int(golden.prioridad),
                "activo": 1 if golden.activo else 0,
                "errores": json.dumps(golden.errores_que_previene, ensure_ascii=False),
            },
        )
        return int(result.lastrowid or 0)

    def listar_activas(self, limite: int = 50) -> list[GoldenConversation]:
        rows = self._s.execute(
            text(GoldenConversationsSql.LISTAR_ACTIVAS), {"limite": int(limite)}
        ).mappings().all()
        return [GoldenConversationMapper.from_row(dict(r)) for r in rows]

    def buscar_por_categoria(
        self, categoria: str, intencion: str | None = None, limite: int = 5
    ) -> list[GoldenConversation]:
        rows = self._s.execute(
            text(GoldenConversationsSql.POR_CATEGORIA),
            {"cat": categoria, "intencion": intencion, "limite": int(limite)},
        ).mappings().all()
        return [GoldenConversationMapper.from_row(dict(r)) for r in rows]

    def desactivar(self, caso_que_cubre: str) -> None:
        self._s.execute(text(GoldenConversationsSql.DESACTIVAR), {"caso": caso_que_cubre})

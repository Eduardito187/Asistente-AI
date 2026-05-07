from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.conversaciones_fallidas import (
    ConversacionFallida,
    ConversacionesFallidasRepository,
)
from .mappers.conversacion_fallida_mapper import ConversacionFallidaMapper
from .sql.conversaciones_fallidas_sql import ConversacionesFallidasSql


class MariaDbConversacionesFallidasRepository(ConversacionesFallidasRepository):
    """Impl MariaDB del repo ConversacionesFallidas."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def guardar(self, conv: ConversacionFallida) -> None:
        self._s.execute(
            text(ConversacionesFallidasSql.INSERT),
            {
                "sid": str(conv.sesion_id) if conv.sesion_id else None,
                "msg": conv.mensaje_usuario[:2000] if conv.mensaje_usuario else None,
                "perfil": json.dumps(conv.perfil_estado, default=str, ensure_ascii=False),
                "args": json.dumps(conv.ultimo_buscar_args, default=str, ensure_ascii=False) if conv.ultimo_buscar_args else None,
                "razon": conv.razon_fallo[:64],
                "trace": (conv.trace_resumen or "")[:2000] or None,
            },
        )

    def listar_recientes(self, limite: int = 50) -> list[ConversacionFallida]:
        rows = self._s.execute(
            text(ConversacionesFallidasSql.LISTAR_RECIENTES), {"limite": int(limite)}
        ).mappings().all()
        return [ConversacionFallidaMapper.from_row(dict(r)) for r in rows]

    def contar_por_razon(self) -> dict[str, int]:
        rows = self._s.execute(text(ConversacionesFallidasSql.CONTAR_POR_RAZON)).mappings().all()
        return {r["razon_fallo"]: int(r["total"]) for r in rows}

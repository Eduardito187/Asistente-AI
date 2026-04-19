from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.conversaciones_curadas import (
    ConversacionCurada,
    ConversacionesCuradasRepository,
)
from .sql import ConversacionCuradaSql


class MariaDbConversacionesCuradasRepository(ConversacionesCuradasRepository):
    """Impl MariaDB del repo de ConversacionCurada."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def guardar(self, conv: ConversacionCurada) -> int:
        res = self._s.execute(
            text(ConversacionCuradaSql.INSERTAR),
            self._a_params(conv) | {"sesion_id": self._sesion_str(conv.sesion_id)},
        )
        return int(res.lastrowid or 0)

    def actualizar(self, conv: ConversacionCurada) -> None:
        self._s.execute(
            text(ConversacionCuradaSql.ACTUALIZAR),
            self._a_params(conv) | {"id": conv.id},
        )

    def por_sesion(self, sesion_id: UUID) -> ConversacionCurada | None:
        row = self._s.execute(
            text(ConversacionCuradaSql.POR_SESION),
            {"sesion_id": str(sesion_id)},
        ).mappings().first()
        return self._desde_row(row) if row else None

    def top_activas(self, limite: int) -> list[ConversacionCurada]:
        rows = self._s.execute(
            text(ConversacionCuradaSql.TOP_ACTIVAS), {"limite": int(limite)}
        ).mappings().all()
        return [self._desde_row(r) for r in rows]

    def listar(self, limite: int, offset: int) -> list[ConversacionCurada]:
        rows = self._s.execute(
            text(ConversacionCuradaSql.LISTAR),
            {"limite": int(limite), "offset": int(offset)},
        ).mappings().all()
        return [self._desde_row(r) for r in rows]

    def set_activa(self, id_: int, activa: bool) -> None:
        self._s.execute(
            text(ConversacionCuradaSql.SET_ACTIVA),
            {"id": id_, "activa": 1 if activa else 0},
        )

    @staticmethod
    def _a_params(conv: ConversacionCurada) -> dict:
        return {
            "etiqueta": conv.etiqueta,
            "cliente": conv.cliente_texto,
            "asistente": conv.asistente_texto,
            "score": int(conv.score),
            "turnos": int(conv.turnos),
            "llevo": 1 if conv.llevo_a_orden else 0,
            "activa": 1 if conv.activa else 0,
        }

    @staticmethod
    def _sesion_str(sid: UUID | None) -> str | None:
        return str(sid) if sid else None

    @staticmethod
    def _desde_row(row) -> ConversacionCurada:
        sid = row["sesion_id"]
        return ConversacionCurada(
            id=row["id"],
            sesion_id=UUID(sid) if sid else None,
            etiqueta=row["etiqueta"],
            cliente_texto=row["cliente_texto"],
            asistente_texto=row["asistente_texto"],
            score=row["score"],
            turnos=row["turnos"],
            llevo_a_orden=bool(row["llevo_a_orden"]),
            activa=bool(row["activa"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

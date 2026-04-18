from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.chat import ChatRepository, Mensaje, RolMensaje
from .sql import ChatSql


class MariaDbChatRepository(ChatRepository):

    def __init__(self, session: Session) -> None:
        self._s = session

    def guardar(self, mensaje: Mensaje) -> None:
        self._s.execute(
            text(ChatSql.GUARDAR_MENSAJE),
            {
                "s": str(mensaje.sesion_id),
                "r": mensaje.rol.value,
                "c": mensaje.contenido,
            },
        )

    def historial(self, sesion_id: UUID, limite: int) -> list[Mensaje]:
        rows = self._s.execute(
            text(ChatSql.HISTORIAL), {"s": str(sesion_id), "n": limite}
        ).mappings().all()
        return [
            Mensaje(
                sesion_id=sesion_id,
                rol=RolMensaje(r["rol"]),
                contenido=r["contenido"],
                created_at=r["created_at"],
            )
            for r in reversed(rows)
        ]

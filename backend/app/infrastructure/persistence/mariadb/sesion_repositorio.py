from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.sesiones import Sesion, SesionRepository
from .mappers import SesionMapper
from .sql import SesionSql


class MariaDbSesionRepository(SesionRepository):

    def __init__(self, session: Session) -> None:
        self._s = session

    def crear(self, sesion: Sesion) -> None:
        self._s.execute(
            text(SesionSql.CREAR),
            {"id": str(sesion.id), "estado": sesion.estado.value},
        )

    def obtener(self, sesion_id: UUID) -> Optional[Sesion]:
        row = self._s.execute(
            text(SesionSql.POR_ID), {"id": str(sesion_id)}
        ).mappings().first()
        return SesionMapper.from_row(dict(row)) if row else None

    def existe(self, sesion_id: UUID) -> bool:
        return bool(
            self._s.execute(
                text(SesionSql.EXISTE), {"id": str(sesion_id)}
            ).scalar()
        )

    def guardar(self, sesion: Sesion) -> None:
        self._s.execute(
            text(SesionSql.ACTUALIZAR),
            {
                "estado": sesion.estado.value,
                "n": sesion.cliente_nombre,
                "e": sesion.cliente_email,
                "t": sesion.cliente_telefono,
                "ult": sesion.ultima_actividad_at,
                "id": str(sesion.id),
            },
        )

    def tocar(self, sesion_id: UUID) -> None:
        self._s.execute(text(SesionSql.TOCAR), {"id": str(sesion_id)})

    def marcar_abandonadas(self, umbral_horas: int) -> int:
        res = self._s.execute(
            text(SesionSql.MARCAR_ABANDONADAS), {"h": umbral_horas}
        )
        return res.rowcount or 0

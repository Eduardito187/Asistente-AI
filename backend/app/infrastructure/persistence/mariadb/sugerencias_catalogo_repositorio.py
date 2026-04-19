from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.sugerencias_catalogo import SugerenciaCatalogo, SugerenciasCatalogoRepository
from .sql import SugerenciaCatalogoSql


class MariaDbSugerenciasCatalogoRepository(SugerenciasCatalogoRepository):
    """Impl MariaDB del repo de SugerenciaCatalogo."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def por_nombre_norm(self, nombre_norm: str) -> Optional[SugerenciaCatalogo]:
        row = self._s.execute(
            text(SugerenciaCatalogoSql.POR_NOMBRE_NORM),
            {"nombre_norm": nombre_norm},
        ).mappings().first()
        if not row:
            return None
        return SugerenciaCatalogo(
            id=row["id"],
            nombre=row["nombre"],
            nombre_norm=row["nombre_norm"],
            categoria_estimada=row["categoria_estimada"],
            marca_estimada=row["marca_estimada"],
            veces_solicitado=row["veces_solicitado"],
            primer_contexto_cliente=row["primer_contexto_cliente"],
            primera_fecha=row["primera_fecha"],
            ultima_fecha=row["ultima_fecha"],
        )

    def insertar(self, sugerencia: SugerenciaCatalogo) -> int:
        res = self._s.execute(
            text(SugerenciaCatalogoSql.INSERTAR),
            {
                "nombre": sugerencia.nombre,
                "nombre_norm": sugerencia.nombre_norm,
                "categoria": sugerencia.categoria_estimada,
                "marca": sugerencia.marca_estimada,
                "contexto": sugerencia.primer_contexto_cliente,
            },
        )
        return int(res.lastrowid or 0)

    def incrementar(self, nombre_norm: str) -> None:
        self._s.execute(
            text(SugerenciaCatalogoSql.INCREMENTAR),
            {"nombre_norm": nombre_norm},
        )

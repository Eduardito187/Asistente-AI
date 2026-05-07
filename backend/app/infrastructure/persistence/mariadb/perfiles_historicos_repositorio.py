from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.perfiles_historicos import (
    PerfilHistorico,
    PerfilesHistoricosRepository,
)
from .mappers.perfil_historico_mapper import PerfilHistoricoMapper
from .sql.perfiles_historicos_sql import PerfilesHistoricosSql


class MariaDbPerfilesHistoricosRepository(PerfilesHistoricosRepository):
    """Impl MariaDB del repo PerfilesHistoricos."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def upsert(self, perfil: PerfilHistorico) -> None:
        self._s.execute(
            text(PerfilesHistoricosSql.UPSERT),
            {
                "hash": perfil.contacto_hash,
                "snap": json.dumps(perfil.perfil_snapshot, default=str, ensure_ascii=False),
                "cat": perfil.ultima_categoria,
                "marca": perfil.ultima_marca,
                "sku": perfil.ultima_compra_sku,
            },
        )

    def obtener_por_contacto_hash(self, contacto_hash: str) -> PerfilHistorico | None:
        row = self._s.execute(
            text(PerfilesHistoricosSql.POR_HASH), {"hash": contacto_hash}
        ).mappings().first()
        return PerfilHistoricoMapper.from_row(dict(row)) if row else None

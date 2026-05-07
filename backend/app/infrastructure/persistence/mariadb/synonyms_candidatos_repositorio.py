from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.synonyms_candidatos import (
    SynonymCandidato,
    SynonymsCandidatosRepository,
)
from .mappers.synonym_candidato_mapper import SynonymCandidatoMapper
from .sql.synonyms_candidatos_sql import SynonymsCandidatosSql


class MariaDbSynonymsCandidatosRepository(SynonymsCandidatosRepository):
    """Impl MariaDB del repo SynonymsCandidatos."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def upsert_incrementando(self, termino: str, categoria_inferida: str | None) -> int:
        clean = (termino or "").strip().lower()[:120]
        if not clean:
            return 0
        self._s.execute(
            text(SynonymsCandidatosSql.UPSERT),
            {"termino": clean, "cat": (categoria_inferida or None)},
        )
        row = self._s.execute(
            text(SynonymsCandidatosSql.OBTENER_OCURRENCIAS),
            {"termino": clean},
        ).mappings().first()
        return int(row["ocurrencias"]) if row else 0

    def listar_top(self, limite: int = 50, solo_no_promovidos: bool = True) -> list[SynonymCandidato]:
        rows = self._s.execute(
            text(SynonymsCandidatosSql.LISTAR_TOP),
            {"limite": int(limite), "solo_no_promovidos": 1 if solo_no_promovidos else 0},
        ).mappings().all()
        return [SynonymCandidatoMapper.from_row(dict(r)) for r in rows]

    def marcar_promovido(self, id_: int) -> None:
        self._s.execute(text(SynonymsCandidatosSql.MARCAR_PROMOVIDO), {"id_": int(id_)})

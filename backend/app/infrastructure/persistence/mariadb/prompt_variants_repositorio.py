from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.prompt_variants import PromptVariant, PromptVariantsRepository
from .mappers.prompt_variant_mapper import PromptVariantMapper
from .sql.prompt_variants_sql import PromptVariantsSql


class MariaDbPromptVariantsRepository(PromptVariantsRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def listar_activas(self) -> list[PromptVariant]:
        rows = self._s.execute(text(PromptVariantsSql.LISTAR_ACTIVAS)).mappings().all()
        return [PromptVariantMapper.from_row(dict(r)) for r in rows]

    def upsert(self, variant: PromptVariant) -> None:
        self._s.execute(
            text(PromptVariantsSql.UPSERT),
            {
                "name": variant.variant_name,
                "extra": variant.prompt_extra,
                "weight": int(variant.weight),
                "activa": 1 if variant.activa else 0,
                "desc": variant.descripcion,
            },
        )

    def desactivar(self, variant_name: str) -> None:
        self._s.execute(text(PromptVariantsSql.DESACTIVAR), {"name": variant_name})

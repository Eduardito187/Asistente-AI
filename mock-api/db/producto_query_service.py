from __future__ import annotations

from typing import Optional

from sqlalchemy import text

from .engine import engine
from .sql import ProductoSql


class ProductoQueryService:
    """Ejecuta las consultas de producto del mock-api contra MySQL."""

    @staticmethod
    def listar(where: str = "", params: Optional[dict] = None) -> list[dict]:
        with engine.connect() as conn:
            rows = conn.execute(text(ProductoSql.select(where)), params or {}).mappings().all()
        return [dict(r) for r in rows]

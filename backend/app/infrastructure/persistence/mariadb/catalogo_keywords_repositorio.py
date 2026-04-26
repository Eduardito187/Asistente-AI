from __future__ import annotations

from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.catalogo import (
    CatalogoKeywordsRepository,
    CategoriaRelacionada,
    CategoriaSinonimo,
)
from .sql import CatalogoKeywordsSql


class MariaDbCatalogoKeywordsRepository(CatalogoKeywordsRepository):
    """Impl MariaDB del repo del vocabulario del catalogo."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def buscar_sinonimo_exacto(
        self, palabra_norm: str
    ) -> Optional[CategoriaSinonimo]:
        row = self._s.execute(
            text(CatalogoKeywordsSql.SINONIMO_POR_PALABRA_NORM),
            {"palabra": palabra_norm},
        ).mappings().first()
        return self._fila_a_sinonimo(row) if row else None

    def buscar_sinonimos_por_tokens(
        self, tokens_norm: list[str], limite: int = 5
    ) -> list[CategoriaSinonimo]:
        if not tokens_norm:
            return []
        params: dict = {f"t{i}": t for i, t in enumerate(tokens_norm)}
        params["limite"] = max(1, min(limite, 20))
        rows = self._s.execute(
            text(CatalogoKeywordsSql.sinonimos_por_tokens_in(len(tokens_norm))),
            params,
        ).mappings().all()
        return [self._fila_a_sinonimo(r) for r in rows]

    def buscar_sinonimos_por_primer_token(
        self, primer_token: str, limite: int = 30
    ) -> list[CategoriaSinonimo]:
        """Sinónimos multi-palabra que empiezan con primer_token exacto.
        Útil para tokens cortos como 'air' → 'air fryer', 'air m3', etc."""
        rows = self._s.execute(
            text(CatalogoKeywordsSql.SINONIMOS_FRASE_PRIMER_TOKEN),
            {"prefijo_frase": f"{primer_token} %", "limite": max(1, min(limite, 50))},
        ).mappings().all()
        return [self._fila_a_sinonimo(r) for r in rows]

    def buscar_sinonimos_fuzzy(
        self, token_norm: str, limite: int = 10
    ) -> list[CategoriaSinonimo]:
        """Pool amplio de candidatos por prefijo de 2 chars + longitud similar.
        Prefijo corto tolera typos que cambian el tercer char (cocinas->cosinas,
        lavadora->labadora). El caller filtra por ratio de similitud."""
        if len(token_norm) < 4:
            return []
        prefix_len = 2
        rows = self._s.execute(
            text(CatalogoKeywordsSql.SINONIMOS_PREFIJO_FUZZY),
            {
                "prefijo": token_norm[:prefix_len],
                "prefix_len": prefix_len,
                "token_len": len(token_norm),
                "limite": max(1, min(limite, 50)),
            },
        ).mappings().all()
        return [self._fila_a_sinonimo(r) for r in rows]

    def buscar_relacionadas(
        self, categoria_origen: str, limite: int = 5
    ) -> list[CategoriaRelacionada]:
        rows = self._s.execute(
            text(CatalogoKeywordsSql.RELACIONES_POR_ORIGEN),
            {"origen": categoria_origen.lower(), "limite": max(1, min(limite, 20))},
        ).mappings().all()
        return [
            CategoriaRelacionada(
                categoria_origen=r["categoria_origen"],
                categoria_sugerida=r["categoria_sugerida"],
                subcategoria_sugerida=r["subcategoria_sugerida"],
                razon=r["razon"],
                prioridad=int(r["prioridad"]),
            )
            for r in rows
        ]

    def skus_por_keyword(
        self, keyword_norm: str, limite: int = 10
    ) -> list[str]:
        rows = self._s.execute(
            text(CatalogoKeywordsSql.SKUS_POR_KEYWORD),
            {"kw": keyword_norm, "limite": max(1, min(limite, 20))},
        ).scalars().all()
        return list(rows)

    @staticmethod
    def _fila_a_sinonimo(row) -> CategoriaSinonimo:
        return CategoriaSinonimo(
            palabra_clave=row["palabra_clave"],
            palabra_clave_norm=row["palabra_clave_norm"],
            categoria=row["categoria"],
            subcategoria=row["subcategoria"],
            confianza=float(row["confianza"]),
            sku_especifico=row.get("sku_especifico"),
        )

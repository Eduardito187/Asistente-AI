from __future__ import annotations

from .....domain.synonyms_candidatos import SynonymCandidato


class SynonymCandidatoMapper:
    """Materializa un SynonymCandidato desde un row crudo."""

    @staticmethod
    def from_row(r: dict) -> SynonymCandidato:
        return SynonymCandidato(
            id=r["id"],
            termino=r.get("termino") or "",
            categoria_inferida=r.get("categoria_inferida"),
            ocurrencias=int(r.get("ocurrencias") or 0),
            primera_vez=r["primera_vez"],
            ultima_vez=r["ultima_vez"],
            promovido=bool(r.get("promovido")),
        )

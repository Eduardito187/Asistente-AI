from __future__ import annotations

from .....domain.negative_patterns import NegativePattern


class NegativePatternMapper:
    @staticmethod
    def from_row(r: dict) -> NegativePattern:
        return NegativePattern(
            id=r["id"],
            patron=r["patron"],
            reason_code=r.get("reason_code"),
            descripcion=r.get("descripcion"),
            activo=bool(r.get("activo")),
            ocurrencias_observadas=int(r.get("ocurrencias_observadas") or 0),
            created_at=r.get("created_at"),
        )

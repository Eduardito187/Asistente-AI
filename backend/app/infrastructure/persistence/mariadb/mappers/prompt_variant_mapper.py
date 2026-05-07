from __future__ import annotations

from .....domain.prompt_variants import PromptVariant


class PromptVariantMapper:
    @staticmethod
    def from_row(r: dict) -> PromptVariant:
        return PromptVariant(
            id=r["id"],
            variant_name=r["variant_name"],
            prompt_extra=r.get("prompt_extra") or "",
            weight=int(r.get("weight") or 50),
            activa=bool(r.get("activa")),
            descripcion=r.get("descripcion"),
            created_at=r.get("created_at"),
        )

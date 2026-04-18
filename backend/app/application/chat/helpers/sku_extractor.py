from __future__ import annotations

from typing import Any


class SkuExtractor:
    """Extrae y deduplica SKUs desde resultados de tool-calls."""

    @staticmethod
    def extraer(result: Any) -> list[str]:
        """Extrae SKUs de un dict de resultado de tool, en cualquier forma."""
        if not isinstance(result, dict):
            return []
        out: list[str] = []
        if isinstance(result.get("sku"), str):
            out.append(result["sku"])
        for p in result.get("productos") or []:
            if isinstance(p, dict) and p.get("sku"):
                out.append(p["sku"])
        for it in result.get("items") or []:
            if isinstance(it, dict) and it.get("sku"):
                out.append(it["sku"])
        return out

    @staticmethod
    def dedupe(items: list[str]) -> list[str]:
        """Elimina duplicados preservando el orden de aparicion."""
        seen: set[str] = set()
        result: list[str] = []
        for s in items:
            if s not in seen:
                seen.add(s)
                result.append(s)
        return result

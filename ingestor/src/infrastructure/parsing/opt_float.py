from __future__ import annotations


class OptFloat:
    """Parseo seguro de string opcional a float."""

    @staticmethod
    def parse(v: str | None) -> float | None:
        """Parsea un string opcional a float; devuelve None si vacio o None."""
        s = (v or "").strip()
        return float(s) if s else None

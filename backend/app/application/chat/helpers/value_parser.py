from __future__ import annotations

import json
from typing import Any


class ValueParser:
    """Coerciones seguras de valores arbitrarios provenientes del LLM."""

    @staticmethod
    def a_float(v: Any) -> float | None:
        """Convierte un valor arbitrario a float o None si no es parseable."""
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def a_int(v: Any) -> int | None:
        """Convierte un valor arbitrario a int (aceptando '8', 8.0, 8). Tolera decimales con truncado."""
        if v is None or v == "":
            return None
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def a_bool(v: Any) -> bool | None:
        """Convierte un valor arbitrario a bool. Acepta bool nativo y strings
        'true'/'false'/'1'/'0'/'si'/'no'. Devuelve None si no es interpretable."""
        if v is None or v == "":
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        texto = str(v).strip().lower()
        if texto in ("true", "1", "si", "sí", "yes"):
            return True
        if texto in ("false", "0", "no"):
            return False
        return None

    @staticmethod
    def parse_args(raw: Any) -> dict:
        """Normaliza los arguments del tool-call a dict Python."""
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                return {}
        return raw or {}

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EjecutarIngestaCommand:
    """Gatilla una ingesta completa desde el adaptador inyectado."""

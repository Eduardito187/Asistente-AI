from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ReglaMentira:
    """Regla (tool, patron) que indica cuando el LLM afirma haber hecho algo."""

    tool: str
    patron: re.Pattern[str]

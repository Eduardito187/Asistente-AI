from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class PromptVariant:
    """Variante de prompt para A/B testing en runtime (#15 del review).
    `prompt_extra` es texto que se concatena despues de SYSTEM_PROMPT base."""

    id: Optional[int]
    variant_name: str
    prompt_extra: str
    weight: int
    activa: bool
    descripcion: Optional[str]
    created_at: Optional[datetime] = None

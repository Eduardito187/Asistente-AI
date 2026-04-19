from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RespuestaFeedback:
    """DTO: rating inferido (1-5) + comentario textual."""

    rating: int
    comentario: str

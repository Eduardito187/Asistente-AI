from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompararProductosQuery:
    """Query: compara 2-4 SKUs lado a lado para ayudar a decidir."""

    skus: tuple[str, ...]

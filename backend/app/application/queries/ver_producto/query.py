from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VerProductoQuery:
    """Query: ver detalle de un producto por SKU."""

    sku: str

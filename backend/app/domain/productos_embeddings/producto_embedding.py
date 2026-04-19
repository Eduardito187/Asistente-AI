from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProductoEmbedding:
    """Vector de embedding serializado para un SKU del catalogo."""

    sku: str
    modelo: str
    vector: bytes
    updated_at: datetime

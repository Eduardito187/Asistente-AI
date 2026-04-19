from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RespuestaSkuDirecta:
    """Respuesta pre-generada cuando el cliente pego un SKU valido."""

    sku: str
    texto: str
    producto: dict = field(default_factory=dict)

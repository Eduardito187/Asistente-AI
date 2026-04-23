from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CategoriaSinonimo:
    """Entrada de vocabulario: mapea una palabra libre (lo que el cliente dice)
    a una categoria real del catalogo, o a un SKU concreto cuando el alias
    identifica univocamente un producto (ej. 's26 ultra' -> SM-S948BZKKBVO).
    SRP: ser la fuente estructurada para interpretar terminos antes de que
    el LLM improvise."""

    palabra_clave: str
    palabra_clave_norm: str
    categoria: str
    subcategoria: Optional[str]
    confianza: float
    sku_especifico: Optional[str] = None

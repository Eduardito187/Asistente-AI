from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CategoriaSinonimo:
    """Entrada de vocabulario: mapea una palabra libre (lo que el cliente dice)
    a una categoria real del catalogo. SRP: ser la fuente estructurada para
    interpretar terminos antes de que el LLM improvise."""

    palabra_clave: str
    palabra_clave_norm: str
    categoria: str
    subcategoria: Optional[str]
    confianza: float

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RegistrarSynonymCandidatoCommand:
    """Comando: registra una palabra que el usuario uso pero no resolvio,
    incrementa contador y devuelve count actual para que el caller decida
    si dispara una accion (alerta, auto-promocion, etc.)."""

    termino: str
    categoria_inferida: Optional[str] = None

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class PerfilHistorico:
    """Snapshot persistente del PerfilSesion ligado a un contacto (email/phone
    hasheado). Permite que el cliente recurrente reanude su contexto pasado."""

    id: Optional[int]
    contacto_hash: str
    perfil_snapshot: dict
    ultima_categoria: Optional[str]
    ultima_marca: Optional[str]
    ultima_compra_sku: Optional[str]
    visitas: int
    primera_vez: datetime
    ultima_vez: datetime

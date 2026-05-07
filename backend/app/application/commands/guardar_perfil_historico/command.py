from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GuardarPerfilHistoricoCommand:
    """Comando: persiste snapshot del PerfilSesion ligado a un contacto
    hasheado. Tipicamente disparado al confirmar orden con email/telefono."""

    contacto_hash: str
    perfil_snapshot: dict
    ultima_categoria: Optional[str]
    ultima_marca: Optional[str]
    ultima_compra_sku: Optional[str]

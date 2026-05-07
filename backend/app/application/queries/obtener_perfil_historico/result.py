from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ResultadoObtenerPerfilHistorico:
    encontrado: bool
    perfil_snapshot: dict
    ultima_categoria: Optional[str] = None
    ultima_marca: Optional[str] = None
    ultima_compra_sku: Optional[str] = None
    visitas: int = 0

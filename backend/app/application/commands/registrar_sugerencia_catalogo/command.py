from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RegistrarSugerenciaCatalogoCommand:
    """Comando: registra (o incrementa) un producto real pedido por un cliente
    que aún no está en el catálogo."""

    nombre: str
    categoria_estimada: Optional[str]
    marca_estimada: Optional[str]
    contexto_cliente: Optional[str]

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class RespuestaProductoAusente:
    """Resultado del `ManejadorProductoAusente`: texto para el cliente y
    alternativas reales a mostrar.

    `categoria_ofrecida` permite a ProcesarChatService anclar en el perfil
    la alternativa que le dijimos al cliente, para que turnos siguientes
    ('hay motos?') confirmen coherentemente en vez de volver a negar."""

    texto: str
    productos_alternativos: List[dict]
    skus_alternativos: List[str]
    sugerencia_registrada: bool
    categoria_ofrecida: Optional[str] = None
    subcategoria_ofrecida: Optional[str] = None

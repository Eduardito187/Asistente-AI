from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from ..shared.errors import ReglaDeNegocioViolada
from .datos_cliente import DatosCliente
from .estado_orden import EstadoOrden
from .orden_item import OrdenItem


@dataclass
class Orden:
    """Raíz del agregado Orden."""

    id: UUID
    numero_orden: Optional[str]  # lo asigna la BD via DEFAULT con SEQUENCE
    sesion_id: UUID
    cliente: DatosCliente
    items: List[OrdenItem]
    estado: EstadoOrden
    notas: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.items:
            raise ReglaDeNegocioViolada("no se puede crear una orden sin items")

    @property
    def total_bob(self) -> float:
        return round(sum(i.subtotal_bob for i in self.items), 2)

    @property
    def items_cantidad(self) -> int:
        return sum(i.cantidad for i in self.items)

    @staticmethod
    def nueva(
        sesion_id: UUID,
        cliente: DatosCliente,
        items: List[OrdenItem],
        notas: Optional[str] = None,
    ) -> "Orden":
        return Orden(
            id=uuid4(),
            numero_orden=None,
            sesion_id=sesion_id,
            cliente=cliente,
            items=items,
            estado=EstadoOrden.CONFIRMADA,
            notas=notas,
        )

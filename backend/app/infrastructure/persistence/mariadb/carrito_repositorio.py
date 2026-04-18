from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.carritos import Carrito, CarritoRepository
from ....domain.productos import SKU
from .mappers import CarritoItemMapper
from .sql import CarritoSql


class MariaDbCarritoRepository(CarritoRepository):

    def __init__(self, session: Session) -> None:
        self._s = session

    def obtener(self, sesion_id: UUID) -> Carrito:
        rows = self._s.execute(
            text(CarritoSql.OBTENER_ITEMS), {"s": str(sesion_id)}
        ).mappings().all()
        items = [CarritoItemMapper.from_row(dict(r)) for r in rows]
        return Carrito(sesion_id=sesion_id, items=items)

    def agregar_o_incrementar(self, sesion_id: UUID, sku: SKU, cantidad: int) -> None:
        self._s.execute(
            text(CarritoSql.AGREGAR_O_INCREMENTAR),
            {"s": str(sesion_id), "sku": str(sku), "c": cantidad},
        )

    def quitar(self, sesion_id: UUID, sku: SKU) -> bool:
        res = self._s.execute(
            text(CarritoSql.QUITAR_ITEM),
            {"s": str(sesion_id), "sku": str(sku)},
        )
        return bool(res.rowcount)

    def vaciar(self, sesion_id: UUID) -> None:
        self._s.execute(text(CarritoSql.VACIAR), {"s": str(sesion_id)})

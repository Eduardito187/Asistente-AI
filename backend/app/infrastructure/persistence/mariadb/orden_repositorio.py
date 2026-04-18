from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.ordenes import Orden, OrdenRepository
from .mappers import OrdenItemMapper, OrdenMapper
from .sql import OrdenSql


class MariaDbOrdenRepository(OrdenRepository):

    def __init__(self, session: Session) -> None:
        self._s = session

    def persistir(self, orden: Orden) -> Orden:
        self._s.execute(
            text(OrdenSql.INSERTAR_ORDEN),
            {
                "id": str(orden.id),
                "sid": str(orden.sesion_id),
                "n": orden.cliente.nombre,
                "e": orden.cliente.email,
                "t": orden.cliente.telefono,
                "tot": orden.total_bob,
                "c": orden.items_cantidad,
                "estado": orden.estado.value,
                "notas": orden.notas,
            },
        )
        for item in orden.items:
            self._s.execute(
                text(OrdenSql.INSERTAR_ITEM),
                {
                    "o": str(orden.id),
                    "sku": str(item.sku),
                    "nom": item.nombre,
                    "m": item.marca,
                    "c": item.cantidad,
                    "pu": item.precio_unitario.monto,
                    "sub": item.subtotal_bob,
                },
            )
        self._s.flush()
        row = self._s.execute(
            text(OrdenSql.RELEER_NUMERO_Y_FECHA), {"id": str(orden.id)}
        ).mappings().first()
        if row:
            orden.numero_orden = row["numero_orden"]
            orden.created_at = row["created_at"]
        return orden

    def obtener_por_numero(self, numero_orden: str) -> Optional[Orden]:
        row = self._s.execute(
            text(OrdenSql.POR_NUMERO), {"n": numero_orden}
        ).mappings().first()
        if not row:
            return None
        return OrdenMapper.from_row(dict(row), self._cargar_items(str(row["id"])))

    def listar_por_sesion(self, sesion_id: UUID) -> List[Orden]:
        rows = self._s.execute(
            text(OrdenSql.POR_SESION), {"s": str(sesion_id)}
        ).mappings().all()
        return [
            OrdenMapper.from_row(dict(r), self._cargar_items(str(r["id"])))
            for r in rows
        ]

    def listar(self, limite: int = 50) -> List[Orden]:
        rows = self._s.execute(
            text(OrdenSql.LISTAR), {"l": limite}
        ).mappings().all()
        return [
            OrdenMapper.from_row(dict(r), self._cargar_items(str(r["id"])))
            for r in rows
        ]

    def _cargar_items(self, orden_id: str) -> list:
        rows = self._s.execute(
            text(OrdenSql.CARGAR_ITEMS), {"o": orden_id}
        ).mappings().all()
        return [OrdenItemMapper.from_row(dict(r)) for r in rows]

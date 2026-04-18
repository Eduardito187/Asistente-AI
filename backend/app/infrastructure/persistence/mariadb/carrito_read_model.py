from __future__ import annotations

from typing import Optional

from sqlalchemy import text

from ....application.ports.read_models import CarritoReadModel
from ..engine import engine
from .sql import CarritoReadSql


class MariaDbCarritoReadModel(CarritoReadModel):
    """Lectura pura sobre vista_carritos."""

    def listar(self, estado: Optional[str], solo_con_items: bool, limite: int) -> list[dict]:
        sql, params = CarritoReadSql.listar(estado=estado, solo_con_items=solo_con_items)
        params["l"] = limite
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()
        return [
            {
                "sesion_id": r["sesion_id"],
                "estado": r["estado"],
                "cliente_nombre": r["cliente_nombre"],
                "cliente_email": r["cliente_email"],
                "cliente_telefono": r["cliente_telefono"],
                "items": int(r["items"]),
                "total_bob": float(r["total_bob"] or 0),
                "ultima_actividad_at": (
                    r["ultima_actividad_at"].isoformat() if r["ultima_actividad_at"] else None
                ),
            }
            for r in rows
        ]

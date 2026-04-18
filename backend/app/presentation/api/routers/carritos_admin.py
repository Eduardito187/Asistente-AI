from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ....application.commands.marcar_carritos_abandonados import (
    MarcarCarritosAbandonadosCommand,
    MarcarCarritosAbandonadosHandler,
)
from ....application.queries.listar_carritos import ListarCarritosHandler, ListarCarritosQuery
from ....domain.sesiones import EstadoCarrito
from ..deps import listar_carritos_handler, marcar_abandonados_handler

router = APIRouter(prefix="/carritos", tags=["carritos-admin"])


@router.get("")
def listar(
    estado: Optional[str] = Query(default=None),
    solo_con_items: bool = Query(default=False),
    limite: int = Query(default=100, ge=1, le=500),
    handler: ListarCarritosHandler = Depends(listar_carritos_handler),
):
    estado_vo = EstadoCarrito(estado) if estado else None
    filas = handler.ejecutar(
        ListarCarritosQuery(estado=estado_vo, solo_con_items=solo_con_items, limite=limite)
    )
    return {"carritos": filas}


@router.post("/abandonados")
def marcar_abandonados(
    horas: int = Query(default=24, ge=1, le=720),
    handler: MarcarCarritosAbandonadosHandler = Depends(marcar_abandonados_handler),
):
    cantidad = handler.ejecutar(MarcarCarritosAbandonadosCommand(umbral_horas=horas))
    return {"marcados_abandonados": cantidad, "umbral_horas": horas}

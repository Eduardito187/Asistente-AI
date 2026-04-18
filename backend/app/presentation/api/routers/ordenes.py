from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ....application.commands.confirmar_orden import (
    ConfirmarOrdenCommand,
    ConfirmarOrdenHandler,
)
from ....application.queries.listar_ordenes import ListarOrdenesHandler, ListarOrdenesQuery
from ....application.queries.obtener_orden import ObtenerOrdenHandler, ObtenerOrdenQuery
from ....application.queries.ver_ordenes_sesion import (
    VerOrdenesSesionHandler,
    VerOrdenesSesionQuery,
)
from ....domain.shared.errors import DomainError, EntidadNoEncontrada, ReglaDeNegocioViolada
from ..deps import (
    confirmar_handler,
    listar_ordenes_handler,
    obtener_orden_handler,
    ver_ordenes_sesion_handler,
)
from ..mappers import OrdenApiMapper
from ..schemas import ConfirmarOrdenIn, OrdenDetalle, OrdenResumen

router = APIRouter(prefix="/ordenes", tags=["ordenes"])


@router.post("/{sesion_id}", response_model=OrdenDetalle)
def confirmar(
    sesion_id: UUID,
    payload: ConfirmarOrdenIn,
    handler: ConfirmarOrdenHandler = Depends(confirmar_handler),
    obtener: ObtenerOrdenHandler = Depends(obtener_orden_handler),
):
    try:
        res = handler.ejecutar(
            ConfirmarOrdenCommand(
                sesion_id=sesion_id,
                cliente_nombre=payload.cliente_nombre,
                cliente_email=payload.cliente_email,
                cliente_telefono=payload.cliente_telefono,
                notas=payload.notas,
            )
        )
    except ReglaDeNegocioViolada as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DomainError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    orden = obtener.ejecutar(ObtenerOrdenQuery(numero_orden=res.numero_orden))
    if orden is None:
        raise HTTPException(status_code=500, detail="orden recien creada no encontrada")
    return OrdenApiMapper.detalle(orden)


@router.get("", response_model=list[OrdenResumen])
def listar(
    limite: int = Query(default=50, ge=1, le=500),
    handler: ListarOrdenesHandler = Depends(listar_ordenes_handler),
):
    ordenes = handler.ejecutar(ListarOrdenesQuery(limite=limite))
    return [OrdenApiMapper.resumen(o) for o in ordenes]


@router.get("/sesion/{sesion_id}", response_model=list[OrdenResumen])
def por_sesion(
    sesion_id: UUID,
    handler: VerOrdenesSesionHandler = Depends(ver_ordenes_sesion_handler),
):
    ordenes = handler.ejecutar(VerOrdenesSesionQuery(sesion_id=sesion_id))
    return [OrdenApiMapper.resumen(o) for o in ordenes]


@router.get("/{numero_orden}", response_model=OrdenDetalle)
def obtener(
    numero_orden: str,
    handler: ObtenerOrdenHandler = Depends(obtener_orden_handler),
):
    orden = handler.ejecutar(ObtenerOrdenQuery(numero_orden=numero_orden))
    if orden is None:
        raise HTTPException(status_code=404, detail=f"orden {numero_orden} no encontrada")
    return OrdenApiMapper.detalle(orden)

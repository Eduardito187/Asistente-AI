from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ....application.commands.agregar_al_carrito import (
    AgregarAlCarritoCommand,
    AgregarAlCarritoHandler,
)
from ....application.commands.quitar_del_carrito import (
    QuitarDelCarritoCommand,
    QuitarDelCarritoHandler,
)
from ....application.commands.vaciar_carrito import (
    VaciarCarritoCommand,
    VaciarCarritoHandler,
)
from ....application.queries.ver_carrito import VerCarritoHandler, VerCarritoQuery
from ....domain.shared.errors import DomainError, EntidadNoEncontrada
from ..deps import agregar_handler, quitar_handler, vaciar_handler, ver_carrito_handler
from ..schemas import CartItemIn, CartItemOut, CartView

router = APIRouter(prefix="/carrito", tags=["carrito"])


@router.get("/{sesion_id}", response_model=CartView)
def ver(sesion_id: UUID, handler: VerCarritoHandler = Depends(ver_carrito_handler)):
    carrito = handler.ejecutar(VerCarritoQuery(sesion_id=sesion_id))
    items = [
        CartItemOut(
            sku=str(i.sku),
            nombre=i.nombre,
            cantidad=i.cantidad,
            precio_unitario_bob=i.precio_unitario.monto,
            subtotal_bob=i.subtotal_bob,
        )
        for i in carrito.items
    ]
    return CartView(sesion_id=sesion_id, items=items, total_bob=carrito.total_bob)


@router.post("/{sesion_id}/agregar")
def agregar(
    sesion_id: UUID,
    payload: CartItemIn,
    handler: AgregarAlCarritoHandler = Depends(agregar_handler),
):
    try:
        res = handler.ejecutar(
            AgregarAlCarritoCommand(
                sesion_id=sesion_id, sku=payload.sku, cantidad=payload.cantidad
            )
        )
    except EntidadNoEncontrada as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DomainError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "sku": res.sku,
        "nombre": res.nombre,
        "cantidad_agregada": res.cantidad_agregada,
        "precio_unitario_bob": res.precio_unitario_bob,
    }


@router.delete("/{sesion_id}/{sku}")
def quitar(
    sesion_id: UUID,
    sku: str,
    handler: QuitarDelCarritoHandler = Depends(quitar_handler),
):
    try:
        handler.ejecutar(QuitarDelCarritoCommand(sesion_id=sesion_id, sku=sku))
    except EntidadNoEncontrada as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DomainError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@router.delete("/{sesion_id}")
def vaciar(sesion_id: UUID, handler: VaciarCarritoHandler = Depends(vaciar_handler)):
    handler.ejecutar(VaciarCarritoCommand(sesion_id=sesion_id))
    return {"ok": True}

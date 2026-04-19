from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ....application.commands.activar_conversacion_curada import (
    ActivarConversacionCuradaCommand,
    ActivarConversacionCuradaHandler,
)
from ....application.queries.listar_conversaciones_curadas import (
    ListarConversacionesCuradasHandler,
    ListarConversacionesCuradasQuery,
)
from ..deps import activar_conversacion_curada_handler, listar_conversaciones_curadas_handler

router = APIRouter(prefix="/conversaciones_curadas", tags=["conversaciones-curadas-admin"])


@router.get("")
def listar(
    limite: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    handler: ListarConversacionesCuradasHandler = Depends(listar_conversaciones_curadas_handler),
):
    filas = handler.ejecutar(ListarConversacionesCuradasQuery(limite=limite, offset=offset))
    return {
        "conversaciones": [
            {
                "id": c.id,
                "sesion_id": str(c.sesion_id) if c.sesion_id else None,
                "etiqueta": c.etiqueta,
                "cliente_texto": c.cliente_texto,
                "asistente_texto": c.asistente_texto,
                "score": c.score,
                "turnos": c.turnos,
                "llevo_a_orden": c.llevo_a_orden,
                "activa": c.activa,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in filas
        ],
        "limite": limite,
        "offset": offset,
    }


@router.post("/{id_}/activar")
def activar(
    id_: int,
    activa: bool = Query(default=True),
    handler: ActivarConversacionCuradaHandler = Depends(activar_conversacion_curada_handler),
):
    handler.ejecutar(ActivarConversacionCuradaCommand(id=id_, activa=activa))
    return {"id": id_, "activa": activa}

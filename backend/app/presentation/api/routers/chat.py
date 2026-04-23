from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ....application.services.procesar_chat_service import ChatInput, ProcesarChatService
from ..deps import procesar_chat_service
from ..schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    service: ProcesarChatService = Depends(procesar_chat_service),
):
    if not req.mensaje.strip():
        raise HTTPException(status_code=400, detail="el mensaje no puede estar vacio")
    try:
        out = await service.procesar(ChatInput(mensaje=req.mensaje, sesion_id=req.sesion_id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ChatResponse(
        sesion_id=out.sesion_id,
        respuesta=out.respuesta,
        productos_citados=out.productos_citados,
        productos_sugeridos=out.productos_sugeridos,
        pasos=out.pasos,
    )

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ....application.services.procesar_chat_service import ChatInput, ProcesarChatService
from ..deps import procesar_chat_service
from ..middlewares.rate_limiter import SessionRateLimiter
from ..schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

_rate_limiter = SessionRateLimiter(max_requests=60, ventana_segundos=60.0)


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    service: ProcesarChatService = Depends(procesar_chat_service),
):
    _rate_limiter.verificar(str(req.sesion_id))
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

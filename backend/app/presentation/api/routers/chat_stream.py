from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ....application.services.procesar_chat_service import ChatInput, ProcesarChatService
from ..deps import procesar_chat_service
from ..schemas import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])

DELAY_TOKEN_SEG = 0.015


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    service: ProcesarChatService = Depends(procesar_chat_service),
):
    if not req.mensaje.strip():
        raise HTTPException(status_code=400, detail="el mensaje no puede estar vacio")
    try:
        out = await service.procesar(ChatInput(mensaje=req.mensaje, sesion_id=req.sesion_id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    async def gen() -> AsyncIterator[bytes]:
        async for evento in _emitir(out):
            yield evento

    return StreamingResponse(gen(), media_type="text/event-stream")


async def _emitir(out) -> AsyncIterator[bytes]:
    for token in _tokenizar(out.respuesta):
        yield _sse("token", {"texto": token})
        await asyncio.sleep(DELAY_TOKEN_SEG)
    yield _sse(
        "meta",
        {
            "sesion_id": str(out.sesion_id),
            "productos_citados": out.productos_citados,
            "pasos": out.pasos,
        },
    )
    yield _sse("done", {})


def _tokenizar(texto: str) -> list[str]:
    """Parte el texto preservando separadores para recomponerlo en el cliente."""
    tokens: list[str] = []
    buffer = ""
    for ch in texto:
        if ch in (" ", "\n", "\t"):
            if buffer:
                tokens.append(buffer)
                buffer = ""
            tokens.append(ch)
        else:
            buffer += ch
    if buffer:
        tokens.append(buffer)
    return tokens


def _sse(evento: str, data: dict) -> bytes:
    return f"event: {evento}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")

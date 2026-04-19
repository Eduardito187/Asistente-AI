from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .presentation.api.deps import llm_port
from .presentation.api.errors import registrar as registrar_errores
from .presentation.api.routers import (
    carrito,
    carritos_admin,
    chat,
    chat_stream,
    conversaciones_curadas_admin,
    embeddings_admin,
    health,
    metricas,
    ordenes,
    productos,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await llm_port().warmup()
    yield


app = FastAPI(title="Asistente AI Dismac", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_errores(app)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(chat_stream.router)
app.include_router(productos.router)
app.include_router(carrito.router)
app.include_router(ordenes.router)
app.include_router(carritos_admin.router)
app.include_router(conversaciones_curadas_admin.router)
app.include_router(metricas.router)
app.include_router(embeddings_admin.router)

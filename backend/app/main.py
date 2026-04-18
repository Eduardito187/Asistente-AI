from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .presentation.api.errors import registrar as registrar_errores
from .presentation.api.routers import (
    carrito,
    carritos_admin,
    chat,
    health,
    ordenes,
    productos,
)

app = FastAPI(title="Asistente AI Dismac", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_errores(app)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(productos.router)
app.include_router(carrito.router)
app.include_router(ordenes.router)
app.include_router(carritos_admin.router)

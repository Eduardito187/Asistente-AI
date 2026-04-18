"""Composition root del Mock API Dismac.

Expone:
- REST:    GET /health, GET /productos, GET /productos/{sku}, GET /productos.csv
- GraphQL: POST /graphql
"""
from __future__ import annotations

from fastapi import FastAPI

from graphql_api import graphql_router
from rest import health, listar_productos, obtener_producto, productos_csv

app = FastAPI(title="Mock API Dismac", version="0.1.0")
app.include_router(graphql_router, prefix="/graphql")
app.include_router(health.router)
app.include_router(listar_productos.router)
app.include_router(obtener_producto.router)
app.include_router(productos_csv.router)

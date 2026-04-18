from __future__ import annotations

from fastapi import APIRouter, HTTPException

from db import ProductoQueryService

router = APIRouter()


@router.get("/productos/{sku}")
def obtener_producto(sku: str):
    rows = ProductoQueryService.listar("p.sku = :sku", {"sku": sku})
    if not rows:
        raise HTTPException(404, f"SKU {sku} no encontrado")
    return rows[0]

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from db import ProductoQueryService

router = APIRouter()


@router.get("/productos")
def listar_productos(categoria: Optional[str] = None, marca: Optional[str] = None):
    clauses, params = [], {}
    if categoria:
        clauses.append("(c.slug = :cat OR c.nombre = :cat)")
        params["cat"] = categoria
    if marca:
        clauses.append("m.nombre = :marca")
        params["marca"] = marca
    where = " AND ".join(clauses)
    return ProductoQueryService.listar(where, params)

from __future__ import annotations

from fastapi import APIRouter, Query

from ....application.queries.cobertura_atributos import (
    CoberturaAtributosHandler,
    CoberturaAtributosQuery,
)
from ..deps import uow_factory

router = APIRouter(prefix="/admin/cobertura_atributos", tags=["cobertura"])


def _handler() -> CoberturaAtributosHandler:
    return CoberturaAtributosHandler(uow_factory)


@router.get("")
def get_cobertura(por_categoria: bool = Query(False)):
    """Porcentaje de productos con cada columna estructurada poblada.
    Con `por_categoria=true` devuelve el desglose por categoría."""
    resultado = _handler().ejecutar(CoberturaAtributosQuery(por_categoria=por_categoria))
    global_ = resultado.global_
    return {
        "total_productos": global_.total,
        "cobertura_global": global_.porcentajes,
        "por_categoria": [
            {
                "categoria": f.categoria,
                "total": f.total,
                "cobertura": f.porcentajes,
            }
            for f in resultado.por_categoria
        ],
    }


@router.post("/enriquecer")
def enriquecer_batch(limite: int = Query(500, ge=1, le=5000)):
    """Dispara el extractor regex sobre productos con columnas vacías.
    Parsea nombre + descripcion y rellena los campos que pueda inferir.
    Idempotente: usa COALESCE, nunca sobreescribe valores existentes."""
    return _handler().enriquecer_batch(limite=limite)

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ....application.queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery
from ....application.queries.listar_categorias import ListarCategoriasHandler, ListarCategoriasQuery
from ....application.queries.ver_producto import VerProductoHandler, VerProductoQuery
from ..deps import buscar_handler, listar_categorias_handler, ver_producto_handler
from ..mappers import ProductoApiMapper
from ..schemas import ProductoOut

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("", response_model=list[ProductoOut])
def buscar(
    q: Optional[str] = Query(default=None),
    categoria: Optional[str] = None,
    subcategoria: Optional[str] = None,
    marca: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    solo_con_stock: bool = True,
    limite: int = 20,
    handler: BuscarProductosHandler = Depends(buscar_handler),
):
    productos = handler.ejecutar(
        BuscarProductosQuery(
            query=q,
            categoria=categoria,
            subcategoria=subcategoria,
            marca=marca,
            precio_min=precio_min,
            precio_max=precio_max,
            solo_con_stock=solo_con_stock,
            limite=limite,
        )
    )
    return [ProductoApiMapper.out(p) for p in productos]


@router.get("/categorias")
def categorias(handler: ListarCategoriasHandler = Depends(listar_categorias_handler)):
    return {"categorias": handler.ejecutar(ListarCategoriasQuery())}


@router.get("/{sku}", response_model=ProductoOut)
def obtener(sku: str, handler: VerProductoHandler = Depends(ver_producto_handler)):
    res = handler.ejecutar(VerProductoQuery(sku=sku))
    if res.producto is None:
        raise HTTPException(status_code=404, detail={"sku_no_encontrado": sku, "similares": res.skus_similares})
    return ProductoApiMapper.out(res.producto)

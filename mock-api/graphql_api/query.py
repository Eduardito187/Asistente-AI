from __future__ import annotations

from typing import List, Optional

import strawberry

from db import ProductoQueryService

from .producto import Producto
from .producto_graphql_mapper import ProductoGraphqlMapper


@strawberry.type
class Query:
    @strawberry.field
    def productos(self, categoria: Optional[str] = None) -> List[Producto]:
        if categoria:
            rows = ProductoQueryService.listar(
                "c.slug = :slug OR c.nombre = :slug", {"slug": categoria}
            )
        else:
            rows = ProductoQueryService.listar()
        return [ProductoGraphqlMapper.from_row(r) for r in rows]

    @strawberry.field
    def producto(self, sku: str) -> Optional[Producto]:
        rows = ProductoQueryService.listar("p.sku = :sku", {"sku": sku})
        return ProductoGraphqlMapper.from_row(rows[0]) if rows else None

from __future__ import annotations

from typing import Iterable

import httpx

from ...application.ports import SourceAdapter
from ...domain.productos import ProductoInvalido, ProductoRaw


_QUERY = """
query {
  productos {
    sku
    nombre
    descripcion
    categoria
    marca
    precioBob
    precioAnteriorBob
    stock
    imagenUrl
    activo
  }
}
"""


class GraphqlAdapter(SourceAdapter):
    name = "graphql"

    def __init__(self, url: str) -> None:
        self._url = url

    def fetch(self) -> Iterable[ProductoRaw]:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(self._url, json={"query": _QUERY})
            resp.raise_for_status()
            payload = resp.json()
        if "errors" in payload:
            raise RuntimeError(f"GraphQL errors: {payload['errors']}")
        for r in payload["data"]["productos"]:
            try:
                yield ProductoRaw(
                    sku=r["sku"],
                    nombre=r["nombre"],
                    descripcion=r.get("descripcion"),
                    categoria=r.get("categoria"),
                    subcategoria=None,
                    marca=r.get("marca"),
                    precio_bob=float(r["precioBob"]),
                    precio_anterior_bob=(
                        float(r["precioAnteriorBob"])
                        if r.get("precioAnteriorBob") is not None
                        else None
                    ),
                    stock=int(r.get("stock") or 0),
                    imagen_url=r.get("imagenUrl"),
                    url_producto=None,
                    activo=bool(r.get("activo", True)),
                )
            except ProductoInvalido:
                continue

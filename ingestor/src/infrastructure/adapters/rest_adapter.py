from __future__ import annotations

from typing import Iterable

import httpx

from ...application.ports import SourceAdapter
from ...domain.productos import ProductoInvalido, ProductoRaw


class RestAdapter(SourceAdapter):
    name = "rest"

    def __init__(self, url: str) -> None:
        self._url = url

    def fetch(self) -> Iterable[ProductoRaw]:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(self._url)
            resp.raise_for_status()
            data = resp.json()
        for r in data:
            try:
                yield ProductoRaw(
                    sku=r["sku"],
                    nombre=r["nombre"],
                    descripcion=r.get("descripcion"),
                    categoria=r.get("categoria"),
                    subcategoria=r.get("subcategoria"),
                    marca=r.get("marca"),
                    precio_bob=float(r["precio_bob"]),
                    precio_anterior_bob=(
                        float(r["precio_anterior_bob"])
                        if r.get("precio_anterior_bob") is not None
                        else None
                    ),
                    stock=int(r.get("stock") or 0),
                    imagen_url=r.get("imagen_url"),
                    url_producto=r.get("url_producto"),
                    activo=bool(r.get("activo", True)),
                )
            except ProductoInvalido:
                continue

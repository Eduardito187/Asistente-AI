from __future__ import annotations

import csv
from typing import Iterable

from ...application.ports import SourceAdapter
from ...domain.productos import ProductoInvalido, ProductoRaw
from ..parsing import OptFloat


class CsvAdapter(SourceAdapter):
    name = "csv"

    def __init__(self, path: str) -> None:
        self._path = path

    def fetch(self) -> Iterable[ProductoRaw]:
        with open(self._path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    yield ProductoRaw(
                        sku=r["sku"],
                        nombre=r["nombre"],
                        descripcion=r.get("descripcion") or None,
                        categoria=r.get("categoria") or None,
                        subcategoria=None,
                        marca=r.get("marca") or None,
                        precio_bob=float(r["precio_bob"]),
                        precio_anterior_bob=OptFloat.parse(r.get("precio_anterior_bob", "")),
                        stock=int(r.get("stock") or 0),
                        imagen_url=r.get("imagen_url") or None,
                        url_producto=None,
                        activo=(r.get("activo", "1") in ("1", "true", "True", "TRUE")),
                    )
                except ProductoInvalido:
                    continue

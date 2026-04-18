from __future__ import annotations

from typing import Iterable

from sqlalchemy import create_engine, text

from ...application.ports import SourceAdapter
from ...domain.productos import ProductoInvalido, ProductoRaw
from ..persistence.sql import ProductoSql


class MysqlSourceAdapter(SourceAdapter):
    """Lee del MySQL 'origen' (ERP simulado)."""

    name = "mysql"

    def __init__(self, url: str) -> None:
        self._engine = create_engine(url, pool_pre_ping=True)

    def fetch(self) -> Iterable[ProductoRaw]:
        with self._engine.connect() as conn:
            rows = conn.execute(text(ProductoSql.LEER_ERP)).mappings().all()
        for r in rows:
            try:
                yield ProductoRaw(
                    sku=r["sku"],
                    nombre=r["nombre"],
                    descripcion=r["descripcion"],
                    categoria=r["categoria"],
                    subcategoria=None,
                    marca=r["marca"],
                    precio_bob=float(r["precio_bob"]),
                    precio_anterior_bob=(
                        float(r["precio_anterior_bob"])
                        if r["precio_anterior_bob"] is not None
                        else None
                    ),
                    stock=int(r["stock"] or 0),
                    imagen_url=r["imagen_url"],
                    url_producto=None,
                    activo=bool(r["activo"]),
                )
            except ProductoInvalido:
                continue

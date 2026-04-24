"""Adaptador del feed CSV público de Dismac (Facebook Catalog Feed)."""
from __future__ import annotations

import csv
import logging
from typing import Iterable

from typing import Optional

from ...application.ports import SourceAdapter
from ...domain.atributos import ExtractorAtributos
from ...domain.clasificacion import Clasificador
from ...domain.productos import ProductoInvalido, ProductoRaw
from ...domain.texto import NormalizadorTexto
from .akeneo_enriquecedor import AkeneoEnriquecedor

log = logging.getLogger("ingestor.dismac_csv")

# Permitir registros gigantes del feed (descripciones HTML largas).
csv.field_size_limit(10_000_000)


class DismacCsvAdapter(SourceAdapter):

    name = "dismac_csv"

    def __init__(
        self,
        path: str,
        clasificador: Clasificador,
        enriquecedor: Optional[AkeneoEnriquecedor] = None,
    ) -> None:
        self._path = path
        self._clasificador = clasificador
        self._norm = NormalizadorTexto
        self._enriquecedor = enriquecedor

    def fetch(self) -> Iterable[ProductoRaw]:
        log.info("Leyendo feed Dismac desde %s", self._path)
        total = emitidos = descartados = 0
        with open(self._path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total += 1
                if not self._fila_viva(row):
                    descartados += 1
                    continue
                try:
                    producto = self._construir(row)
                except ProductoInvalido:
                    descartados += 1
                    continue
                if producto is None:
                    descartados += 1
                    continue
                if self._enriquecedor:
                    producto = self._enriquecedor.enriquecer(producto)
                emitidos += 1
                yield producto
        log.info(
            "Feed Dismac: total=%d emitidos=%d descartados=%d",
            total, emitidos, descartados,
        )

    # ---- helpers privados ----

    @staticmethod
    def _fila_viva(row: dict) -> bool:
        status = (row.get("status") or "").strip().lower()
        availability = (row.get("availability") or "").strip().lower()
        return status == "active" and availability == "in stock"

    def _construir(self, row: dict) -> ProductoRaw | None:
        sku = (row.get("id") or "").strip()
        nombre = (row.get("title") or "").strip()
        if not sku or not nombre:
            return None

        precios = self._resolver_precios(row)
        if precios is None:
            return None
        precio_bob, precio_anterior = precios

        descripcion_larga = self._norm.limpiar_html(row.get("rich_text_description"))
        descripcion_corta = self._norm.limpiar_html(row.get("description"))
        descripcion = descripcion_larga or descripcion_corta

        marca = self._norm.marca_normalizada(row.get("brand"))
        categoria, subcategoria = self._clasificador.clasificar(
            nombre, product_type=row.get("product_type"), marca=marca
        )
        atributos = ExtractorAtributos.extraer(nombre, descripcion)

        return ProductoRaw(
            sku=sku,
            nombre=nombre[:500],
            descripcion=descripcion,
            categoria=categoria,
            subcategoria=subcategoria,
            marca=marca,
            precio_bob=precio_bob,
            precio_anterior_bob=precio_anterior,
            stock=self._resolver_stock(row),
            imagen_url=(row.get("image_link") or "").strip() or None,
            url_producto=(row.get("link") or "").strip() or None,
            activo=True,
            atributos=atributos,
        )

    def _resolver_precios(self, row: dict) -> tuple[float, float | None] | None:
        precio = self._norm.precio_bob(row.get("price"))
        sale = self._norm.precio_bob(row.get("sale_price"))
        if sale and precio and sale < precio:
            precio_bob, precio_anterior = sale, precio
        else:
            precio_bob = precio or sale
            precio_anterior = None
        if not precio_bob or precio_bob <= 0:
            return None
        return precio_bob, precio_anterior

    @staticmethod
    def _resolver_stock(row: dict) -> int:
        try:
            return max(0, int(row.get("quantity_to_sell_on_facebook") or 0))
        except (TypeError, ValueError):
            return 1  # 'in stock' sin cantidad → asumimos 1

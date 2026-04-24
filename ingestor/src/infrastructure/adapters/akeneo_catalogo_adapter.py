"""Adaptador que itera el catálogo completo de Akeneo como ProductoRaw.

Produce productos con activo=False y precio_bob=0 (sin precio web).
Usa INSERT IGNORE en el repositorio para no pisar productos del feed web.
"""
from __future__ import annotations

import logging
from typing import Iterable

from ...application.ports import SourceAdapter
from ...domain.clasificacion import Clasificador
from ...domain.productos import ProductoRaw
from .akeneo_enriquecedor import AkeneoEnriquecedor

log = logging.getLogger("ingestor.akeneo_catalogo")


class AkeneoCatalogoAdapter(SourceAdapter):

    name = "akeneo_catalogo"

    def __init__(self, enriquecedor: AkeneoEnriquecedor, clasificador: Clasificador) -> None:
        self._enriquecedor = enriquecedor
        self._clasificador = clasificador

    def fetch(self) -> Iterable[ProductoRaw]:
        log.info("Iniciando iteración catálogo Akeneo completo")
        yield from self._enriquecedor.iterar_catalogo(self._clasificador)

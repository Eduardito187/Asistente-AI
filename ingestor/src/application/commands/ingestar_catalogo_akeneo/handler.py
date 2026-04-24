from __future__ import annotations

import logging

from ...ports import ProductoRepository, SourceAdapter
from .command import IngestarCatalogoAkeneoCommand
from .result import ResultadoCatalogoAkeneo

log = logging.getLogger("ingestor.catalogo_akeneo")


class IngestarCatalogoAkeneoHandler:
    """Inserta productos del catálogo Akeneo que no existen en la DB (INSERT IGNORE)."""

    def __init__(self, adapter: SourceAdapter, repo: ProductoRepository) -> None:
        self._adapter = adapter
        self._repo = repo

    def ejecutar(self, _: IngestarCatalogoAkeneoCommand) -> ResultadoCatalogoAkeneo:
        origen = self._adapter.name
        insertados = omitidos = 0
        for p in self._adapter.fetch():
            try:
                if self._repo.insertar_catalogo(p, origen=origen):
                    insertados += 1
                else:
                    omitidos += 1
            except Exception as exc:
                log.warning("Error insertando %s: %s", p.sku, exc)
                omitidos += 1
        log.info(
            "Catálogo Akeneo -> insertados=%d omitidos(ya existían)=%d",
            insertados, omitidos,
        )
        return ResultadoCatalogoAkeneo(insertados=insertados, omitidos=omitidos)

"""Composition root + loop del ingestor."""
from __future__ import annotations

import logging
import os
import time

from ..application.commands import (
    EjecutarIngestaCommand,
    EjecutarIngestaHandler,
    IngestarCatalogoAkeneoCommand,
    IngestarCatalogoAkeneoHandler,
)
from ..domain.clasificacion import Clasificador
from ..infrastructure.adapters import AkeneoCatalogoAdapter, AdapterFactory
from ..infrastructure.adapters.akeneo_enriquecedor import AkeneoEnriquecedor
from ..infrastructure.config import Settings
from ..infrastructure.persistence import (
    EngineFactory,
    EsperadorBd,
    MariaDbIngestaLog,
    MariaDbProductoRepositorio,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("ingestor")


def main() -> None:
    settings = Settings.desde_entorno()
    engine = EngineFactory.mariadb(settings.mariadb_url())
    EsperadorBd().esperar(engine)

    repo = MariaDbProductoRepositorio(engine)
    log_repo = MariaDbIngestaLog(engine)

    # Paso 1: feed web (Facebook) con enriquecimiento Akeneo
    adapter = AdapterFactory.construir(settings)
    handler = EjecutarIngestaHandler(adapter=adapter, repo=repo, log_repo=log_repo)

    # Paso 2: catálogo completo Akeneo (INSERT IGNORE — no pisa el feed web)
    enriquecedor = AkeneoEnriquecedor(settings.akeneo_csv_path)
    catalogo_adapter = AkeneoCatalogoAdapter(
        enriquecedor=enriquecedor,
        clasificador=Clasificador(),
    )
    catalogo_handler = IngestarCatalogoAkeneoHandler(adapter=catalogo_adapter, repo=repo)

    una_sola_vez = os.environ.get("INGEST_ONE_SHOT", "").lower() in ("1", "true", "yes")

    while True:
        try:
            handler.ejecutar(EjecutarIngestaCommand())
        except Exception:
            log.exception("Ingesta feed web aborto en esta iteracion")
        try:
            catalogo_handler.ejecutar(IngestarCatalogoAkeneoCommand())
        except Exception:
            log.exception("Ingesta catálogo Akeneo aborto en esta iteracion")
        if una_sola_vez:
            log.info("INGEST_ONE_SHOT activo, cerrando.")
            return
        log.info("Durmiendo %ds antes de la proxima ingesta", settings.intervalo_seg)
        time.sleep(settings.intervalo_seg)


if __name__ == "__main__":
    main()

"""Composition root + loop del ingestor."""
from __future__ import annotations

import logging
import os
import time

from ..application.commands import EjecutarIngestaCommand, EjecutarIngestaHandler
from ..infrastructure.adapters import AdapterFactory
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
    adapter = AdapterFactory.construir(settings)
    handler = EjecutarIngestaHandler(adapter=adapter, repo=repo, log_repo=log_repo)

    una_sola_vez = os.environ.get("INGEST_ONE_SHOT", "").lower() in ("1", "true", "yes")

    while True:
        try:
            handler.ejecutar(EjecutarIngestaCommand())
        except Exception:
            log.exception("Ingesta aborto en esta iteracion")
        if una_sola_vez:
            log.info("INGEST_ONE_SHOT activo, cerrando.")
            return
        log.info("Durmiendo %ds antes de la proxima ingesta", settings.intervalo_seg)
        time.sleep(settings.intervalo_seg)


if __name__ == "__main__":
    main()

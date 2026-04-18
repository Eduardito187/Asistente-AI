from __future__ import annotations

import logging
import time

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .sql import IngestaLogSql

log = logging.getLogger("ingestor")


class EsperadorBd:
    """Bloquea hasta que MariaDB responda a un ping o se agoten los intentos."""

    def __init__(self, intentos: int = 30, espera_seg: float = 2.0) -> None:
        self._intentos = intentos
        self._espera = espera_seg

    def esperar(self, engine: Engine) -> None:
        for intento in range(1, self._intentos + 1):
            try:
                with engine.connect() as c:
                    c.execute(text(IngestaLogSql.HEALTH))
                return
            except Exception:
                log.info("Esperando MariaDB... intento %d", intento)
                time.sleep(self._espera)
        raise RuntimeError("MariaDB no respondio a tiempo")

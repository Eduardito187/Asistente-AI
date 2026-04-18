from __future__ import annotations

import logging

from ....domain.productos import ProductoInvalido
from ...ports import IngestaLog, ProductoRepository, SourceAdapter
from .command import EjecutarIngestaCommand
from .result import ResultadoIngesta

log = logging.getLogger("ingestor.ejecutar_ingesta")


class EjecutarIngestaHandler:
    """Orquesta: fetch → upsert por cada producto → desactivar faltantes → cerrar log."""

    def __init__(
        self,
        adapter: SourceAdapter,
        repo: ProductoRepository,
        log_repo: IngestaLog,
    ) -> None:
        self._adapter = adapter
        self._repo = repo
        self._log_repo = log_repo

    def ejecutar(self, _: EjecutarIngestaCommand) -> ResultadoIngesta:
        origen = self._adapter.name
        log_id = self._log_repo.iniciar(origen)
        procesados = 0
        rechazados = 0
        skus_vistos: list[str] = []
        try:
            for p in self._adapter.fetch():
                try:
                    self._repo.upsert(p, origen=origen)
                    skus_vistos.append(p.sku)
                    procesados += 1
                except ProductoInvalido as exc:
                    log.warning("Producto invalido descartado: %s", exc)
                    rechazados += 1
            desactivados = self._repo.desactivar_faltantes(origen, skus_vistos)
            self._log_repo.completar(log_id, procesados)
        except Exception as exc:
            log.exception("Ingesta fallo")
            self._log_repo.fallar(log_id, str(exc))
            raise
        log.info(
            "Ingesta %s -> procesados=%d rechazados=%d desactivados=%d",
            origen, procesados, rechazados, desactivados,
        )
        return ResultadoIngesta(
            origen=origen,
            procesados=procesados,
            rechazados=rechazados,
            desactivados=desactivados,
        )

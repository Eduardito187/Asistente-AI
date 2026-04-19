from __future__ import annotations

import logging
from typing import Callable

from ...ports import UnitOfWork
from .command import RegistrarTurnoMostradoCommand

log = logging.getLogger("registrar_turno_mostrado")


class RegistrarTurnoMostradoHandler:
    """Handler CQRS: persiste los SKUs visibles del turno y su rango de precio.

    No debe romper el chat: si MariaDB falla, solo se loguea."""

    MAX_SKUS = 12

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: RegistrarTurnoMostradoCommand) -> None:
        if not cmd.tiene_datos():
            return
        skus_str = ",".join(cmd.skus[: self.MAX_SKUS])
        precios_validos = [p for p in cmd.precios if p is not None and p > 0]
        precio_min = min(precios_validos) if precios_validos else None
        precio_max = max(precios_validos) if precios_validos else None
        try:
            with self._uow_factory() as uow:
                uow.perfiles_sesion.registrar_turno(
                    sesion_id=cmd.sesion_id,
                    skus_mostrados=skus_str,
                    precio_min=precio_min,
                    precio_max=precio_max,
                )
                uow.commit()
        except Exception as exc:
            log.warning("no se pudo registrar turno mostrado: %s", exc)

from __future__ import annotations

from typing import Callable

from ...ports import UnitOfWork
from .command import MarcarCarritosAbandonadosCommand


class MarcarCarritosAbandonadosHandler:
    """Handler CQRS: transiciona sesiones activas a abandonadas tras N horas."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: MarcarCarritosAbandonadosCommand) -> int:
        with self._uow_factory() as uow:
            cantidad = uow.sesiones.marcar_abandonadas(cmd.umbral_horas)
            uow.commit()
            return cantidad

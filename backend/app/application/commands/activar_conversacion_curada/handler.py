from __future__ import annotations

from typing import Callable

from ...ports import UnitOfWork
from .command import ActivarConversacionCuradaCommand


class ActivarConversacionCuradaHandler:
    """Handler CQRS: cambia el flag `activa` de una conversacion curada."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: ActivarConversacionCuradaCommand) -> None:
        with self._uow_factory() as uow:
            uow.conversaciones_curadas.set_activa(cmd.id, cmd.activa)
            uow.commit()

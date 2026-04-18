from __future__ import annotations

from typing import Callable

from ...ports import UnitOfWork
from .command import VaciarCarritoCommand


class VaciarCarritoHandler:
    """Handler CQRS: elimina todos los items del carrito de la sesion."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: VaciarCarritoCommand) -> None:
        with self._uow_factory() as uow:
            uow.sesiones.tocar(cmd.sesion_id)
            uow.carritos.vaciar(cmd.sesion_id)
            uow.commit()

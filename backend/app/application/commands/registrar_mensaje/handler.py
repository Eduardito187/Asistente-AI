from __future__ import annotations

from typing import Callable

from ....domain.chat import Mensaje
from ...ports import UnitOfWork
from .command import RegistrarMensajeCommand


class RegistrarMensajeHandler:
    """Handler CQRS: guarda el mensaje y toca la sesion."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: RegistrarMensajeCommand) -> None:
        with self._uow_factory() as uow:
            uow.chat.guardar(
                Mensaje(sesion_id=cmd.sesion_id, rol=cmd.rol, contenido=cmd.contenido)
            )
            uow.sesiones.tocar(cmd.sesion_id)
            uow.commit()

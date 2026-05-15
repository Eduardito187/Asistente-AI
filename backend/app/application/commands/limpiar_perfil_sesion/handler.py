from __future__ import annotations

import logging
from typing import Callable

from ...ports import UnitOfWork
from .command import LimpiarPerfilSesionCommand

log = logging.getLogger("limpiar_perfil_sesion")


class LimpiarPerfilSesionHandler:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: LimpiarPerfilSesionCommand) -> None:
        try:
            with self._uow_factory() as uow:
                uow.perfiles_sesion.limpiar(cmd.sesion_id)
                uow.commit()
        except Exception as exc:
            log.warning("no se pudo limpiar perfil: %s", exc)

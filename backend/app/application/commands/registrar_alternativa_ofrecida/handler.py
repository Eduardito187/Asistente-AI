from __future__ import annotations

import logging
from typing import Callable

from ...ports import UnitOfWork
from .command import RegistrarAlternativaOfrecidaCommand

log = logging.getLogger("registrar_alternativa_ofrecida")


class RegistrarAlternativaOfrecidaHandler:
    """Handler CQRS: persiste la alternativa ofrecida en el perfil.

    Silencia errores de BD: no romper el chat si MariaDB falla."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: RegistrarAlternativaOfrecidaCommand) -> None:
        try:
            with self._uow_factory() as uow:
                uow.perfiles_sesion.registrar_alternativa_ofrecida(
                    sesion_id=cmd.sesion_id,
                    alternativa=cmd.formato_guardar(),
                )
                uow.commit()
        except Exception as exc:
            log.warning("no se pudo registrar alternativa ofrecida: %s", exc)

from __future__ import annotations

from typing import Callable
from uuid import UUID

from ....domain.sesiones import Sesion
from ...ports import UnitOfWork
from .command import CrearSesionCommand


class CrearSesionHandler:
    """Handler CQRS: crea una sesion nueva y la persiste."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, _: CrearSesionCommand | None = None) -> UUID:
        sesion = Sesion.nueva()
        with self._uow_factory() as uow:
            uow.sesiones.crear(sesion)
            uow.commit()
        return sesion.id

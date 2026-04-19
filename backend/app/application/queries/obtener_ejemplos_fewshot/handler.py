from __future__ import annotations

import logging
from typing import Callable

from ....domain.conversaciones_curadas import ConversacionCurada
from ...ports import UnitOfWork
from .query import ObtenerEjemplosFewShotQuery

log = logging.getLogger("obtener_ejemplos_fewshot")


class ObtenerEjemplosFewShotHandler:
    """Handler CQRS: devuelve top N conversaciones activas por score."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: ObtenerEjemplosFewShotQuery) -> list[ConversacionCurada]:
        try:
            with self._uow_factory() as uow:
                return uow.conversaciones_curadas.top_activas(max(1, q.limite))
        except Exception as exc:
            log.warning("no se pudieron leer ejemplos few-shot: %s", exc)
            return []

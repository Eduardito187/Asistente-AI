from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

from ....domain.metricas_turno import MetricaTurno
from ...ports import UnitOfWork
from .command import RegistrarMetricaTurnoCommand

log = logging.getLogger("registrar_metrica_turno")


class RegistrarMetricaTurnoHandler:
    """Handler CQRS: persiste una metrica de turno. Fallar no debe tirar el chat."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: RegistrarMetricaTurnoCommand) -> None:
        try:
            metrica = MetricaTurno(
                id=None,
                sesion_id=cmd.sesion_id,
                mensaje_usuario_len=cmd.mensaje_usuario_len,
                respuesta_len=cmd.respuesta_len,
                tool_calls=cmd.tool_calls,
                mentiras_detectadas=cmd.mentiras_detectadas,
                productos_citados=cmd.productos_citados,
                ruta=cmd.ruta,
                tiempo_ms=cmd.tiempo_ms,
                created_at=datetime.utcnow(),
            )
            with self._uow_factory() as uow:
                uow.metricas_turno.registrar(metrica)
                uow.commit()
        except Exception as exc:
            log.warning("no se pudo registrar metrica de turno: %s", exc)

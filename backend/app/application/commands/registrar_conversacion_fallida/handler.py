from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from ....domain.conversaciones_fallidas import ConversacionFallida
from ...ports import UnitOfWork
from .command import RegistrarConversacionFallidaCommand

log = logging.getLogger("registrar_conversacion_fallida")


class RegistrarConversacionFallidaHandler:
    """Handler CQRS: persiste un turno fallido. NO debe romper el chat — si
    falla, solo loguea y sigue."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: RegistrarConversacionFallidaCommand) -> None:
        conv = ConversacionFallida(
            id=None,
            sesion_id=cmd.sesion_id,
            mensaje_usuario=cmd.mensaje_usuario,
            perfil_estado=cmd.perfil_estado,
            ultimo_buscar_args=cmd.ultimo_buscar_args,
            razon_fallo=cmd.razon_fallo,
            trace_resumen=cmd.trace_resumen,
            creado_en=datetime.now(timezone.utc),
        )
        try:
            with self._uow_factory() as uow:
                uow.conversaciones_fallidas.guardar(conv)
                uow.commit()
        except Exception as exc:
            log.warning("no se pudo persistir conversacion fallida: %s", exc)

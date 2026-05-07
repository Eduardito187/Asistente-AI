from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from ....domain.conversaciones_curadas import ConversacionCurada
from ....domain.feedback_turnos import FeedbackTurno, VotoFeedback
from ...ports import UnitOfWork
from .command import RegistrarFeedbackTurnoCommand

log = logging.getLogger("registrar_feedback_turno")


class RegistrarFeedbackTurnoHandler:
    """Handler CQRS: persiste el voto y aplica efectos secundarios:
    - thumbs_up + respuesta no vacia => promueve a ConversacionCurada (si no existia).
    - thumbs_down repetido (>=2) sobre la misma sesion => desactiva su few-shot."""

    UMBRAL_NEGATIVOS_PARA_DESACTIVAR = 2

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: RegistrarFeedbackTurnoCommand) -> int:
        try:
            voto = VotoFeedback(cmd.voto)
        except ValueError:
            return 0
        ahora = datetime.now(timezone.utc)
        fb = FeedbackTurno(
            id=None,
            sesion_id=cmd.sesion_id,
            turno_index=int(cmd.turno_index),
            mensaje_usuario=cmd.mensaje_usuario,
            respuesta_agente=cmd.respuesta_agente,
            voto=voto,
            comentario=cmd.comentario,
            creado_en=ahora,
        )
        try:
            with self._uow_factory() as uow:
                fb_id = uow.feedback_turnos.guardar(fb)
                self._aplicar_efectos(uow, cmd, voto, ahora)
                uow.commit()
                return fb_id
        except Exception as exc:
            log.warning("no se pudo registrar feedback: %s", exc)
            return 0

    def _aplicar_efectos(self, uow, cmd: RegistrarFeedbackTurnoCommand, voto: VotoFeedback, ahora):
        existente = uow.conversaciones_curadas.por_sesion(cmd.sesion_id)
        if voto == VotoFeedback.POSITIVO and existente is None and cmd.respuesta_agente:
            uow.conversaciones_curadas.guardar(ConversacionCurada(
                id=None,
                sesion_id=cmd.sesion_id,
                etiqueta="feedback_positivo",
                cliente_texto=(cmd.mensaje_usuario or "")[:1000],
                asistente_texto=cmd.respuesta_agente[:2000],
                score=80,
                turnos=1,
                llevo_a_orden=False,
                activa=True,
                created_at=ahora,
                updated_at=ahora,
            ))
            return
        if voto == VotoFeedback.NEGATIVO and existente is not None and existente.activa:
            negativos = uow.feedback_turnos.listar_negativos(limite=200)
            count = sum(1 for f in negativos if f.sesion_id == cmd.sesion_id)
            if count >= self.UMBRAL_NEGATIVOS_PARA_DESACTIVAR and existente.id is not None:
                uow.conversaciones_curadas.set_activa(existente.id, False)

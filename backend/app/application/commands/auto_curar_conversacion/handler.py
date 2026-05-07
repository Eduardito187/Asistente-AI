from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from ....domain.aprendizaje import ReasonCode
from ....domain.conversaciones_curadas import ConversacionCurada
from ...ports import UnitOfWork
from ..registrar_conversacion_fallida import (
    RegistrarConversacionFallidaCommand,
    RegistrarConversacionFallidaHandler,
)
from .command import AutoCurarConversacionCommand

log = logging.getLogger("auto_curar_conversacion")


class AutoCurarConversacionHandler:
    """Handler CQRS con QUALITY GATE (#1, #4, #9 del review).

    Antes de persistir como ConversacionCurada, corre AutoQualityScorer
    sobre la (respuesta + productos_citados + perfil_estado). Si alguna
    violacion critica (CATEGORY_MISMATCH, HARD_FILTER_IGNORED,
    TECHNICAL_HALLUCINATION, BACKEND_ERROR_VISIBLE) esta presente, el
    turno NO se cura — en su lugar se registra como conversacion_fallida
    para revision con reason_code=QUALITY_GATE_FAILED."""

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        registrar_fallida: RegistrarConversacionFallidaHandler | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._registrar_fallida = registrar_fallida

    def ejecutar(self, cmd: AutoCurarConversacionCommand) -> bool:
        """Devuelve True si paso el gate y se curo; False si fue rechazado."""
        if not cmd.sesion_id:
            return False
        from ...services.auto_quality_scorer import AutoQualityScorer
        score = AutoQualityScorer.evaluar(
            respuesta=cmd.asistente_texto,
            productos=cmd.productos_citados,
            perfil_estado=cmd.perfil_estado,
        )
        if not score.apto_para_fewshot:
            self._registrar_rechazo(cmd, score)
            return False
        try:
            with self._uow_factory() as uow:
                existente = uow.conversaciones_curadas.por_sesion(cmd.sesion_id)
                if existente is not None:
                    return False
                ahora = datetime.now(timezone.utc)
                conv = ConversacionCurada(
                    id=None,
                    sesion_id=cmd.sesion_id,
                    etiqueta=cmd.etiqueta or "auto_curada",
                    cliente_texto=cmd.cliente_texto[:1000],
                    asistente_texto=cmd.asistente_texto[:2000],
                    score=score.score,
                    turnos=1,
                    llevo_a_orden=False,
                    activa=True,
                    created_at=ahora,
                    updated_at=ahora,
                )
                uow.conversaciones_curadas.guardar(conv)
                uow.commit()
                return True
        except Exception as exc:
            log.warning("no se pudo auto-curar conversacion: %s", exc)
            return False

    def _registrar_rechazo(self, cmd: AutoCurarConversacionCommand, score) -> None:
        if self._registrar_fallida is None:
            return
        try:
            self._registrar_fallida.ejecutar(RegistrarConversacionFallidaCommand(
                sesion_id=cmd.sesion_id,
                mensaje_usuario=cmd.cliente_texto,
                perfil_estado=cmd.perfil_estado,
                ultimo_buscar_args=None,
                razon_fallo=f"quality_score={score.score} violaciones={score.violaciones[:3]}",
                trace_resumen=f"reason_code={score.reason_code.value} severidad={score.severidad.value}",
            ))
        except Exception:
            pass

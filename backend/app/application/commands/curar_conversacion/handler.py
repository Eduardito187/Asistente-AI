from __future__ import annotations

from datetime import datetime
from typing import Callable

from ....domain.conversaciones_curadas import ConversacionCurada
from ...ports import UnitOfWork
from .command import CurarConversacionCommand
from .result import CurarConversacionResult


class CurarConversacionHandler:
    """Handler CQRS: upsert de ConversacionCurada por sesion_id."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: CurarConversacionCommand) -> CurarConversacionResult:
        ahora = datetime.utcnow()
        with self._uow_factory() as uow:
            existente = (
                uow.conversaciones_curadas.por_sesion(cmd.sesion_id)
                if cmd.sesion_id
                else None
            )
            if existente is not None:
                existente.etiqueta = cmd.etiqueta
                existente.cliente_texto = cmd.cliente_texto
                existente.asistente_texto = cmd.asistente_texto
                existente.score = cmd.score
                existente.turnos = cmd.turnos
                existente.llevo_a_orden = cmd.llevo_a_orden
                existente.activa = cmd.activa
                existente.updated_at = ahora
                uow.conversaciones_curadas.actualizar(existente)
                uow.commit()
                return CurarConversacionResult(id=existente.id or 0, creada=False)

            nueva = ConversacionCurada(
                id=None,
                sesion_id=cmd.sesion_id,
                etiqueta=cmd.etiqueta,
                cliente_texto=cmd.cliente_texto,
                asistente_texto=cmd.asistente_texto,
                score=cmd.score,
                turnos=cmd.turnos,
                llevo_a_orden=cmd.llevo_a_orden,
                activa=cmd.activa,
                created_at=ahora,
                updated_at=ahora,
            )
            nuevo_id = uow.conversaciones_curadas.guardar(nueva)
            uow.commit()
            return CurarConversacionResult(id=nuevo_id, creada=True)

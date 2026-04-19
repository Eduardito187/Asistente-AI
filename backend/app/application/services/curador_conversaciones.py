from __future__ import annotations

import logging
from uuid import UUID

from ...domain.chat import Mensaje
from ..commands.curar_conversacion import (
    CurarConversacionCommand,
    CurarConversacionHandler,
)
from .evaluador_conversacion import EvaluadorConversacion

log = logging.getLogger("curador_conversaciones")


class CuradorConversaciones:
    """SRP: decidir si una conversacion merece ser guardada como ejemplo few-shot,
    armar los textos cliente/asistente y persistirla via el command."""

    MAX_LEN_CONDENSADO = 1800

    def __init__(
        self,
        evaluador: EvaluadorConversacion,
        curar: CurarConversacionHandler,
    ) -> None:
        self._evaluador = evaluador
        self._curar = curar

    def evaluar_y_guardar(
        self,
        sesion_id: UUID,
        mensajes: list[Mensaje],
        mentiras_detectadas: int,
        llevo_a_orden: bool,
    ) -> bool:
        puntuacion = self._evaluador.evaluar(mensajes, mentiras_detectadas, llevo_a_orden)
        if not puntuacion.es_buena:
            return False
        cliente_texto = self._condensar([m for m in mensajes if m.rol.value == "user"])
        asistente_texto = self._condensar(
            [m for m in mensajes if m.rol.value == "assistant"]
        )
        if not cliente_texto or not asistente_texto:
            return False
        try:
            self._curar.ejecutar(
                CurarConversacionCommand(
                    sesion_id=sesion_id,
                    etiqueta=", ".join(puntuacion.motivos) or None,
                    cliente_texto=cliente_texto,
                    asistente_texto=asistente_texto,
                    score=puntuacion.score,
                    turnos=puntuacion.turnos,
                    llevo_a_orden=puntuacion.llevo_a_orden,
                    activa=True,
                )
            )
            return True
        except Exception as exc:
            log.warning("no se pudo curar conversacion sesion=%s: %s", sesion_id, exc)
            return False

    def _condensar(self, mensajes: list[Mensaje]) -> str:
        partes = [m.contenido.strip() for m in mensajes if m.contenido.strip()]
        texto = " || ".join(partes)
        if len(texto) > self.MAX_LEN_CONDENSADO:
            return texto[: self.MAX_LEN_CONDENSADO] + "..."
        return texto

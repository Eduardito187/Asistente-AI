from __future__ import annotations

import re

from ...domain.chat import Mensaje
from .puntuacion_conversacion import PuntuacionConversacion

RX_DESAGRADO = re.compile(
    r"\b(no|eso no|nada que ver|mal|error|equivocad|no era eso|ninguno)\b",
    re.IGNORECASE,
)
RX_AGRADECIMIENTO = re.compile(
    r"\b(gracias|perfecto|genial|excelente|bacan|listo|esta bien)\b",
    re.IGNORECASE,
)


class EvaluadorConversacion:
    """SRP: puntuar una conversacion para decidir si sirve como ejemplo few-shot.

    Heuristica simple (sin LLM), pensada para correr rapido y barato al cierre
    de sesion. Componentes del score:
      +50 si llevo_a_orden
      +20 si no hubo mentiras_detectadas
      +10 si turnos <= 6
      +10 si el cliente agradecio o expreso conformidad
      -25 si el cliente mostro desagrado/correccion explicita
      -10 si la respuesta promedio del asistente es muy larga (>500 chars)
    """

    def evaluar(
        self,
        mensajes: list[Mensaje],
        mentiras_detectadas: int,
        llevo_a_orden: bool,
    ) -> PuntuacionConversacion:
        score = 0
        motivos: list[str] = []
        turnos = sum(1 for m in mensajes if m.rol.value == "user")

        if llevo_a_orden:
            score += 50
            motivos.append("cerro_orden")
        if mentiras_detectadas == 0:
            score += 20
            motivos.append("sin_mentiras")
        if turnos <= 6 and turnos > 0:
            score += 10
            motivos.append("conciso")

        texto_cliente = " ".join(m.contenido for m in mensajes if m.rol.value == "user")
        if RX_AGRADECIMIENTO.search(texto_cliente):
            score += 10
            motivos.append("agradecimiento")
        if RX_DESAGRADO.search(texto_cliente):
            score -= 25
            motivos.append("desagrado")

        respuestas = [m.contenido for m in mensajes if m.rol.value == "assistant"]
        if respuestas:
            promedio = sum(len(r) for r in respuestas) / len(respuestas)
            if promedio > 500:
                score -= 10
                motivos.append("respuestas_largas")

        return PuntuacionConversacion(
            score=score,
            turnos=turnos,
            llevo_a_orden=llevo_a_orden,
            motivos=motivos,
        )

from __future__ import annotations

from uuid import UUID

from .clasificador_intencion_turno import ClasificadorIntencionTurno
from .detector_intencion_asesoria import DetectorIntencionAsesoria
from .detector_refinamiento_shown import DetectorRefinamientoShown
from .intencion_turno import IntencionTurno
from .responder_comparacion_mostrados import ResponderComparacionMostrados
from .responder_mas_barato import ResponderMasBarato
from .responder_mas_caro import ResponderMasCaro
from .responder_otra_opcion import ResponderOtraOpcion
from .responder_recomendacion_shown import ResponderRecomendacionShown
from .responder_refinamiento_shown import ResponderRefinamientoShown
from .respuesta_follow_up import RespuestaFollowUp


class GestorFollowUpsContextuales:
    """Orquesta el short-circuit deterministico de follow-ups contextuales.

    Dada la intencion del turno y el estado del perfil, elige el responder
    correcto. Si ninguno aplica o no tiene contexto suficiente, devuelve
    None y el turno cae al LLM. Esto evita que el LLM repita el mismo
    listado ante 'mas barato', 'otra opcion' o 'cual me conviene', que era
    el bug reproducido en la sesion del 2026-04-19."""

    def __init__(
        self,
        responder_mas_barato: ResponderMasBarato,
        responder_mas_caro: ResponderMasCaro,
        responder_otra_opcion: ResponderOtraOpcion,
        responder_comparacion: ResponderComparacionMostrados,
        responder_recomendacion: ResponderRecomendacionShown,
        responder_refinamiento: ResponderRefinamientoShown,
    ) -> None:
        self._mas_barato = responder_mas_barato
        self._mas_caro = responder_mas_caro
        self._otra_opcion = responder_otra_opcion
        self._comparacion = responder_comparacion
        self._recomendacion = responder_recomendacion
        self._refinamiento = responder_refinamiento

    def intentar(self, mensaje: str, sesion_id: UUID) -> RespuestaFollowUp | None:
        refinamiento = DetectorRefinamientoShown.detectar(mensaje)
        if refinamiento is not None:
            respuesta = self._refinamiento.responder(sesion_id, refinamiento)
            if respuesta is not None:
                return respuesta

        intencion = ClasificadorIntencionTurno.clasificar(mensaje)
        marca_indif = DetectorIntencionAsesoria.marca_es_indiferente(mensaje)

        if intencion is IntencionTurno.ALTERNATIVE_CHEAPER:
            return self._mas_barato.responder(sesion_id)
        if intencion is IntencionTurno.ALTERNATIVE_BETTER:
            return self._mas_caro.responder(sesion_id)
        if intencion is IntencionTurno.ALTERNATIVE_OTHER:
            return self._otra_opcion.responder(sesion_id)
        if intencion is IntencionTurno.COMPARISON_REQUEST:
            return self._comparacion.responder(sesion_id)
        if intencion is IntencionTurno.RECOMMENDATION_REQUEST:
            return self._recomendacion.responder(sesion_id, marca_indif)
        return None

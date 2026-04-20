from __future__ import annotations

from .detector_consulta_relativa import DetectorConsultaRelativa, TipoConsultaRelativa
from .detector_intencion_asesoria import DetectorIntencionAsesoria
from .detector_intencion_compra import DetectorIntencionCompra
from .intencion_turno import IntencionTurno


class ClasificadorIntencionTurno:
    """SRP: mapea el mensaje del cliente a una unica IntencionTurno.

    Reusa los detectores ya existentes (consulta relativa, asesoria, compra)
    y los unifica bajo un enum unico para que los responders deterministicos
    puedan decidir si interceptan el turno o delegan al LLM.

    Orden de precedencia (primero gana):
      1) Compra cerrada → PURCHASE_INTENT
      2) Follow-ups contextuales → ALTERNATIVE_* / COMPARISON_REQUEST
      3) Modo asesor → RECOMMENDATION_REQUEST
      4) Fallback → UNKNOWN (deja al LLM)"""

    _MAP_CONSULTA_RELATIVA = {
        TipoConsultaRelativa.MAS_BARATO: IntencionTurno.ALTERNATIVE_CHEAPER,
        TipoConsultaRelativa.MAS_CARO: IntencionTurno.ALTERNATIVE_BETTER,
        TipoConsultaRelativa.OTRA_OPCION: IntencionTurno.ALTERNATIVE_OTHER,
        TipoConsultaRelativa.COMPARAR_MOSTRADOS: IntencionTurno.COMPARISON_REQUEST,
    }

    @classmethod
    def clasificar(cls, texto: str) -> IntencionTurno:
        if not texto:
            return IntencionTurno.UNKNOWN
        if DetectorIntencionCompra.tiene_intencion(texto):
            return IntencionTurno.PURCHASE_INTENT
        relativa = DetectorConsultaRelativa.detectar(texto)
        if relativa is not None:
            return cls._MAP_CONSULTA_RELATIVA[relativa.tipo]
        if DetectorIntencionAsesoria.es_modo_asesor(texto):
            return IntencionTurno.RECOMMENDATION_REQUEST
        return IntencionTurno.UNKNOWN

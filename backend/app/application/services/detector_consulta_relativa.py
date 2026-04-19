from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class TipoConsultaRelativa(str, Enum):
    MAS_BARATO = "mas_barato"
    MAS_CARO = "mas_caro"
    OTRA_OPCION = "otra_opcion"
    COMPARAR_MOSTRADOS = "comparar_mostrados"


@dataclass(frozen=True)
class ConsultaRelativa:
    """Follow-up que se refiere implicitamente al contexto activo del chat."""

    tipo: TipoConsultaRelativa


class DetectorConsultaRelativa:
    """Detecta follow-ups que dependen del contexto previo ('mas barato',
    'otra opcion', 'alguna mas premium', 'comparalos'). Cuando dispara, el
    agente NO debe volver a pedir categoria ni producto: debe reusar los
    filtros del perfil y ajustar lo que corresponda (precio, exclusion de
    SKUs ya mostrados, comparacion).

    Reglas:
      - MAS_BARATO: 'mas barato', 'mas economico', 'alguna mas accesible',
        'mas baja', 'reduce precio', 'no tan caro'.
      - MAS_CARO: 'mas caro', 'mas premium', 'mejor opcion', 'algo top'.
      - OTRA_OPCION: 'otra', 'otras', 'alternativa', 'diferente'.
      - COMPARAR_MOSTRADOS: 'compara los anteriores', 'cual es la diferencia
        entre los que mostraste', 'entre esos cual'."""

    _RX_MAS_BARATO = re.compile(
        r"\b(?:"
        r"mas\s+(?:barat[oa]s?|econ[oó]mic[oa]s?|accesibles?|baratit[oa]s?|bajit[oa]s?|baj[oa]s?)"
        r"|algo\s+(?:mas\s+)?(?:barat[oa]|econ[oó]mic[oa]|accesible)"
        r"|no\s+tan\s+car[oa]"
        r"|(?:bajame|rebaja|reduce|baja)\s+(?:el\s+)?precio"
        r"|(?:dentro\s+de|sobre)\s+(?:lo\s+)?mas\s+(?:barat[oa]|econ[oó]mic[oa])"
        r")\b",
        re.IGNORECASE,
    )
    _RX_MAS_CARO = re.compile(
        r"\b(?:"
        r"mas\s+(?:car[oa]s?|premium|top|completo|potente|avanzad[oa]s?|alt[oa]\s+gama)"
        r"|algo\s+(?:mas\s+)?(?:premium|top|de\s+gama\s+alta|avanzad[oa]|mejor)"
        r"|(?:uno|una|otr[oa])\s+mejor"
        r"|y\s+(?:uno|una)\s+mejor"
        r"|mejor\s+opci[oó]n"
        r"|subile\s+(?:la\s+)?calidad"
        r"|la\s+mejor\s+que\s+tengas"
        r")\b",
        re.IGNORECASE,
    )
    _RX_OTRA_OPCION = re.compile(
        r"\b(?:"
        r"otr[oa]s?\s+(?:opci[oó]n|opciones|modelo|modelos|alternativ[oa]s?)"
        r"|alguna\s+alternativ[ao]"
        r"|una\s+alternativ[ao]"
        r"|alternativas?"
        r"|(?:otro|otros)\s+producto"
        r"|algo\s+diferente"
        r"|diferentes?\s+opciones?"
        r")\b",
        re.IGNORECASE,
    )
    _RX_COMPARAR = re.compile(
        r"\b(?:"
        r"compar(?:a|ame|alos|alas|emos|acion|arlos|arlas)"
        r"|diferencias?\s+entre"
        r"|cual\s+(?:de\s+)?(?:(?:los|las)\s+)?(?:mostrad[oa]s?|anteriores?)"
        r"|entre\s+(?:esos|esas|estos|estas|los\s+que|las\s+que)"
        r")\b",
        re.IGNORECASE,
    )

    @classmethod
    def detectar(cls, texto: str) -> ConsultaRelativa | None:
        if not texto:
            return None
        if cls._RX_COMPARAR.search(texto):
            return ConsultaRelativa(TipoConsultaRelativa.COMPARAR_MOSTRADOS)
        if cls._RX_MAS_BARATO.search(texto):
            return ConsultaRelativa(TipoConsultaRelativa.MAS_BARATO)
        if cls._RX_MAS_CARO.search(texto):
            return ConsultaRelativa(TipoConsultaRelativa.MAS_CARO)
        if cls._RX_OTRA_OPCION.search(texto):
            return ConsultaRelativa(TipoConsultaRelativa.OTRA_OPCION)
        return None

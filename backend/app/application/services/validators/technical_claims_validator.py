from __future__ import annotations

import re

from .category_consistency_validator import ResultadoValidacion
from ....domain.aprendizaje import ReasonCode


class TechnicalClaimsValidator:
    """SRP: detecta afirmaciones tecnicas en la respuesta que NO estan
    en la ficha de los productos citados. Atributos vigilados: HDMI 2.1,
    inverter, IP67/68, ANC, refresh hz especifico, garantia extendida.
    Falla con TECHNICAL_HALLUCINATION si la respuesta los afirma sin
    que el catalogo los tenga."""

    _RX_HDMI21 = re.compile(r"\bhdmi\s*2\.1\b", re.IGNORECASE)
    _RX_INVERTER = re.compile(r"\binverter\b", re.IGNORECASE)
    _RX_IP_RATING = re.compile(r"\bip6[78]\b", re.IGNORECASE)
    _RX_ANC = re.compile(r"\b(anc|cancelaci[oó]n\s+activa)\b", re.IGNORECASE)
    _RX_HZ_PROMISE = re.compile(r"\b(120|144|240)\s*hz\b", re.IGNORECASE)
    _RX_GARANTIA_EXT = re.compile(r"\bgarant[ií]a\s+extendid", re.IGNORECASE)

    @classmethod
    def validar(cls, respuesta: str, productos: list[dict]) -> ResultadoValidacion:
        if not respuesta or not productos:
            return ResultadoValidacion(True, ReasonCode.OK, "sin productos")
        catalogo_texto = " ".join(
            f"{p.get('nombre','')} {p.get('descripcion','')} {p.get('caracteristicas','')}"
            for p in productos
        ).lower()
        if cls._RX_HDMI21.search(respuesta) and "hdmi 2.1" not in catalogo_texto:
            return ResultadoValidacion(False, ReasonCode.TECHNICAL_HALLUCINATION, "afirma HDMI 2.1")
        if cls._RX_INVERTER.search(respuesta) and "inverter" not in catalogo_texto:
            return ResultadoValidacion(False, ReasonCode.TECHNICAL_HALLUCINATION, "afirma inverter")
        if cls._RX_IP_RATING.search(respuesta) and not cls._RX_IP_RATING.search(catalogo_texto):
            return ResultadoValidacion(False, ReasonCode.TECHNICAL_HALLUCINATION, "afirma IP rating")
        if cls._RX_ANC.search(respuesta) and not cls._RX_ANC.search(catalogo_texto):
            return ResultadoValidacion(False, ReasonCode.TECHNICAL_HALLUCINATION, "afirma ANC")
        if cls._RX_GARANTIA_EXT.search(respuesta) and "extendid" not in catalogo_texto:
            return ResultadoValidacion(False, ReasonCode.TECHNICAL_HALLUCINATION, "afirma garantia extendida")
        m_hz = cls._RX_HZ_PROMISE.search(respuesta)
        if m_hz:
            hz = m_hz.group(1)
            if hz not in catalogo_texto and not any(
                str(p.get("refresh_hz") or "") == hz for p in productos
            ):
                return ResultadoValidacion(False, ReasonCode.TECHNICAL_HALLUCINATION, f"afirma {hz}Hz")
        return ResultadoValidacion(True, ReasonCode.OK, "claims tecnicos coherentes")

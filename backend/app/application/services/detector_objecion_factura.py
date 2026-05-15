from __future__ import annotations

import re


class DetectorObjecionFactura:

    _PATRON_SIN_FACTURA = re.compile(
        r"sin\s+factura\s+(cu[aá]nto|sale|me\s+lo\s+das|precio)"
        r"|precio\s+sin\s+factura"
        r"|sin\s+boleta"
        r"|al\s+negro"
        r"|sin\s+comprobante",
        re.IGNORECASE,
    )

    _PATRON_CON_FACTURA = re.compile(
        r"con\s+factura\s+cu[aá]nto"
        r"|necesito\s+factura"
        r"|quiero\s+factura"
        r"|me\s+das\s+factura"
        r"|incluye\s+factura",
        re.IGNORECASE,
    )

    _PATRON_EMPRESARIAL = re.compile(
        r"factura\s+a\s+nombre\s+de"
        r"|factura\s+empresarial"
        r"|nit\s+de\s+mi\s+empresa"
        r"|raz[oó]n\s+social"
        r"|factura\s+para\s+empresa"
        r"|factura\s+corporativa",
        re.IGNORECASE,
    )

    @classmethod
    def es_objecion_factura(cls, mensaje: str) -> bool:
        return cls.tipo(mensaje) is not None

    @classmethod
    def tipo(cls, mensaje: str) -> str | None:
        if cls._PATRON_EMPRESARIAL.search(mensaje):
            return "empresarial"
        if cls._PATRON_CON_FACTURA.search(mensaje):
            return "con_factura"
        if cls._PATRON_SIN_FACTURA.search(mensaje):
            return "sin_factura"
        return None

from __future__ import annotations

import re


class ParserPresupuesto:
    """Detecta el presupuesto declarado por el cliente en un mensaje libre.

    Un numero es un presupuesto si:
      1. Viene precedido por una palabra clave de dinero (presupuesto, tengo,
         gastar, hasta, maximo, etc.), o
      2. Viene seguido de una moneda explicita (bs, bob, bolivianos, $).

    Un numero NUNCA es presupuesto si esta pegado a una unidad no monetaria
    (mAh, GB, TB, KG, L, W, MHz, pulgadas, inch, \"...). Esto evita que
    '30000mAh' o '128gb' se interpreten como dinero.

    Solo devuelve valores dentro del rango [100, 200000] Bs para cortar
    ruido (anios, codigos, SKUs)."""

    _MIN = 100
    _MAX = 200000

    _KW = (
        r"(?:pre[\s-]?supuesto|presu|tengo|gastar\w*|gasto|gastaria|"
        r"max(?:imo)?|hasta|por\s+solo|solo|rango|costar|cuesta\w*|"
        r"valer|valga|vale|monto|llega|alcanza|pagar|pagaria|poner|"
        r"invertir|destinar|disponer)"
    )
    _CURRENCY = r"(?:bs\.?|bob|bolivianos?|\$)"
    _NON_MONEY_UNIT = (
        r"(?:mah|gb|tb|kg|litros?|lts?|mhz|ghz|hz|mp|"
        r"pulgadas?|inch|cm|mm|ml|rpm|fps)"
    )

    _RX_POR_KEYWORD = re.compile(
        rf"\b{_KW}\b\s*(?:de\s+|en\s+|por\s+)?(?:{_CURRENCY}\s*)?"
        rf"([\d][\d\.,]{{2,}})\s*(?:{_CURRENCY}\b)?",
        re.IGNORECASE,
    )
    _RX_POR_MONEDA = re.compile(
        rf"(?<![a-zA-Z])([\d][\d\.,]{{2,}})\s*{_CURRENCY}\b",
        re.IGNORECASE,
    )
    _RX_MONEDA_PREFIJO = re.compile(
        rf"\b{_CURRENCY}\.?\s*([\d][\d\.,]{{2,}})",
        re.IGNORECASE,
    )
    _RX_UNIDAD_NO_MONETARIA = re.compile(
        rf"([\d][\d\.,]{{2,}})\s*{_NON_MONEY_UNIT}\b",
        re.IGNORECASE,
    )

    @classmethod
    def extraer(cls, texto: str) -> float | None:
        if not texto:
            return None
        no_monetarios = cls._numeros_no_monetarios(texto)
        for regex in (cls._RX_POR_KEYWORD, cls._RX_POR_MONEDA, cls._RX_MONEDA_PREFIJO):
            valor = cls._primer_valor_valido(regex, texto, no_monetarios)
            if valor is not None:
                return valor
        return None

    @classmethod
    def _numeros_no_monetarios(cls, texto: str) -> set[str]:
        return {m.group(1) for m in cls._RX_UNIDAD_NO_MONETARIA.finditer(texto)}

    @classmethod
    def _primer_valor_valido(cls, regex: re.Pattern, texto: str, excluidos: set[str]) -> float | None:
        for match in regex.finditer(texto):
            crudo = match.group(1)
            if crudo in excluidos:
                continue
            valor = cls._a_float(crudo)
            if valor is not None and cls._MIN <= valor <= cls._MAX:
                return valor
        return None

    @staticmethod
    def _a_float(crudo: str) -> float | None:
        limpio = crudo.replace(".", "").replace(",", "")
        try:
            return float(limpio)
        except ValueError:
            return None

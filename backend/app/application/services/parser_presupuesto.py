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
        r"pulgadas?|inch|cm|mm|ml|rpm|fps|cc|ccs|%)"
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
    _RX_MIL = re.compile(
        r"\b(\d{1,3})\s*(?:mil|k)\b(?!\s*(?:mah|hz|ghz|mhz|rpm|uhd|p\b))",
        re.IGNORECASE,
    )
    _RX_CONTEXTO_BUDGET = re.compile(
        r"(?:pre[\s-]?supuesto|presu|tengo|gastar\w*|gasto|gastaria|"
        r"max(?:imo)?|hasta|por\s+solo|solo\s+\d|rango|costar|cuesta\w*|"
        r"valer|valga|vale|monto|llega|alcanza|pagar|pagaria|poner|"
        r"invertir|destinar|disponer|bs\.?|bob|bolivianos?|\$)",
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
        valor_mil = cls._extraer_mil(texto)
        if valor_mil is not None:
            return valor_mil
        for regex in (cls._RX_POR_KEYWORD, cls._RX_POR_MONEDA, cls._RX_MONEDA_PREFIJO):
            valor = cls._primer_valor_valido(regex, texto, no_monetarios)
            if valor is not None:
                return valor
        return None

    _RX_IDEAL_VS_MAX = re.compile(
        r"(?:ideal|prefer\w+|me\s+gustar[ia]a|si\s+puedo)[^\d]{0,30}([\d][\d\.,]{2,})"
        r".*?"
        r"(?:max\w*|hasta|podr[ia]a?\s+subir|tope|techo)[^\d]{0,20}([\d][\d\.,]{2,})",
        re.IGNORECASE | re.DOTALL,
    )

    @classmethod
    def extraer_rango(cls, texto: str) -> tuple[float | None, float | None]:
        """Devuelve (presupuesto_ideal, presupuesto_max).

        Si el cliente expresa rango ('ideal 8500, hasta 11000 si vale la pena'),
        ambos valores se devuelven separados. Si solo hay un numero, se asume
        como techo absoluto y el ideal queda None."""
        if not texto:
            return None, None
        m = cls._RX_IDEAL_VS_MAX.search(texto)
        if m:
            v1 = cls._a_float(m.group(1))
            v2 = cls._a_float(m.group(2))
            if v1 and v2 and cls._MIN <= v1 <= cls._MAX and cls._MIN <= v2 <= cls._MAX:
                ideal, techo = (v1, v2) if v1 <= v2 else (v2, v1)
                return ideal, techo
        unico = cls.extraer(texto)
        return None, unico

    @classmethod
    def _extraer_mil(cls, texto: str) -> float | None:
        for match in cls._RX_MIL.finditer(texto):
            inicio = max(0, match.start() - 35)
            fin = min(len(texto), match.end() + 20)
            contexto = texto[inicio:fin]
            if not cls._RX_CONTEXTO_BUDGET.search(contexto):
                continue
            try:
                valor = float(match.group(1)) * 1000.0
            except ValueError:
                continue
            if cls._MIN <= valor <= cls._MAX:
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

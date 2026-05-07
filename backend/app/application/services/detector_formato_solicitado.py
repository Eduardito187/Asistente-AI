from __future__ import annotations

import re

from .formato_solicitado import FormatoSolicitado


class DetectorFormatoSolicitado:
    """SRP: detecta directivas de formato explicitas en el mensaje del
    cliente y las traduce a un VO `FormatoSolicitado`.

    Cubre:
    - Shapes con labels predefinidos:
      * "comprar/evitar/por que"      -> forma="comprar_evitar"
      * "una segura y otra barata"    -> forma="seguro_barato"
      (la forma 'economica/buena/premium' ya esta cubierta por
      `_bloque_formato_tres_opciones`; aca devolvemos None).
    - Tope de productos: "maximo 3", "dame solo 2", "no mas de 3 opciones".
    - Tope de oraciones: "en una frase", "una sola oracion", "corto",
      "no quiero leer mucho".

    Devuelve siempre un VO; usar `vacio()` para saber si aplica."""

    # ---- Forma: comprar / evitar / por que --------------------------------
    _RX_COMPRAR_EVITAR = re.compile(
        r"\b(?:cu[aá]l\s+)?compr(?:ar|aria)\b[^.;\n]*\b(?:cu[aá]l\s+)?(?:evitar|no\s+comprar)\b"
        r"|\b(?:cu[aá]l\s+)?evitar\b[^.;\n]*\b(?:cu[aá]l\s+)?compr(?:ar|aria)\b",
        re.IGNORECASE,
    )

    # ---- Forma: una segura y otra barata ----------------------------------
    # NOTA: NO incluye 'premium' como sinonimo de segura porque el caso
    # 'economica/buena/premium' (3 opciones) ya esta cubierto por
    # `_bloque_formato_tres_opciones`. Si lo agregamos, ambos bloques se
    # renderizan y el LLM se confunde.
    _RX_SEGURO_BARATO = re.compile(
        r"\b(?:una\s+)?(?:opci[oó]n\s+)?(?:segura|confiable)\b"
        r"[^.;\n]{0,40}\b(?:y\s+)?(?:otra\s+|una\s+)?"
        r"(?:barata|econ[oó]mica|accesible)\b"
        r"|\b(?:una\s+)?(?:opci[oó]n\s+)?(?:barata|econ[oó]mica|accesible)\b"
        r"[^.;\n]{0,40}\b(?:y\s+)?(?:otra\s+|una\s+)?"
        r"(?:segura|confiable)\b",
        re.IGNORECASE,
    )

    # ---- Tope de productos: "maximo N opciones", "dame solo N", "no mas de N"
    # Capturamos N en group 1.
    _RX_MAX_PRODUCTOS = re.compile(
        r"\b(?:m[aá]ximo|max|solo|s[oó]lo|nada\s+m[aá]s\s+que|"
        r"no\s+m[aá]s\s+de|hasta)\s+(\d{1,2})\s*"
        r"(?:opciones?|productos?|alternativas?|modelos?|laptops?|"
        r"tel[eé]fonos?|opci|opc)?\b",
        re.IGNORECASE,
    )
    # Variante "dame N" (sin "solo"): "dame 2 opciones"
    _RX_DAME_N = re.compile(
        r"\b(?:dame|mostrame|muestrame|trae|trame|listame)\s+(\d{1,2})\s+"
        r"(?:opciones?|productos?|alternativas?|modelos?)\b",
        re.IGNORECASE,
    )

    # ---- Tope de oraciones: "en una frase", "una oracion", "corto" --------
    _RX_UNA_FRASE = re.compile(
        r"\b(?:en\s+)?(?:una|1)\s+(?:sola\s+)?(?:frase|oraci[oó]n|linea)\b"
        r"|\b(?:respuesta\s+)?corta\b|\bcorto\b"
        r"|\bno\s+quiero\s+leer\s+(?:mucho|nada)\b"
        r"|\bsin\s+(?:tanto|mucho)\s+texto\b",
        re.IGNORECASE,
    )
    _RX_DOS_FRASES = re.compile(
        r"\b(?:en\s+)?(?:dos|2)\s+(?:frases|oraciones|lineas)\b",
        re.IGNORECASE,
    )

    # Senal generica "dame solo:" sin numero — funciona como prefijo a una lista
    # de items (comprar/evitar/etc). No fuerza N pero indica respuesta tersa.
    _RX_DAME_SOLO = re.compile(
        r"\b(?:dame|mostrame|muestrame)\s+s[oó]lo\b\s*:?",
        re.IGNORECASE,
    )

    @classmethod
    def detectar(cls, mensaje: str | None) -> FormatoSolicitado:
        if not mensaje:
            return FormatoSolicitado()
        forma = cls._forma(mensaje)
        max_productos = cls._max_productos(mensaje)
        max_frases = cls._max_frases(mensaje)
        return FormatoSolicitado(
            forma=forma,
            max_productos=max_productos,
            max_frases=max_frases,
        )

    @classmethod
    def _forma(cls, mensaje: str) -> str | None:
        if cls._RX_COMPRAR_EVITAR.search(mensaje):
            return "comprar_evitar"
        if cls._RX_SEGURO_BARATO.search(mensaje):
            return "seguro_barato"
        return None

    @classmethod
    def _max_productos(cls, mensaje: str) -> int | None:
        m = cls._RX_MAX_PRODUCTOS.search(mensaje) or cls._RX_DAME_N.search(mensaje)
        if not m:
            return None
        try:
            valor = int(m.group(1))
        except (ValueError, IndexError):
            return None
        # Topes razonables: 1-5 productos.
        if 1 <= valor <= 5:
            return valor
        return None

    @classmethod
    def _max_frases(cls, mensaje: str) -> int | None:
        if cls._RX_UNA_FRASE.search(mensaje):
            return 1
        if cls._RX_DOS_FRASES.search(mensaje):
            return 2
        # "dame solo:" sin numero -> respuesta breve. Pero si la frase
        # tiene un numero ('dame solo 2 alternativas'), eso ya esta cubierto
        # por max_productos — no inferimos cap de oraciones tambien.
        if cls._RX_DAME_SOLO.search(mensaje) and not cls._RX_MAX_PRODUCTOS.search(mensaje):
            return 2
        return None

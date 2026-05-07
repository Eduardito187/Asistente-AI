from __future__ import annotations

import re


class DetectorMensajesVacios:
    """Detecta mensajes ultra-cortos sin sustancia y rachas de los mismos.

    Caso de uso: el cliente envía 'si', 'ok', '?', '...' repetidamente sin
    contenido — bug del frontend, distracción, o simplemente vagando. Cada
    uno de esos turnos consume tokens del LLM por nada. Si detectamos una
    racha, el bloque de contexto le pide al LLM que NO abra búsqueda y que
    pida al cliente concretar qué necesita."""

    _PALABRAS_VACIAS = frozenset({
        "si", "sí", "no", "ok", "okay", "ya", "ah", "eh", "uh",
        "y", "o", "a", "que", "qué", "como", "cómo",
        "jaja", "jeje", "jiji", "ja", "je", "ji",
        "claro", "dale", "bien", "listo", "perfecto", "genial",
        "mmm", "hmm", "uff", "uy", "ay",
    })
    _SOLO_PUNTUACION = re.compile(r"^[\s\W_]+$")
    _RX_PALABRA = re.compile(r"\w+", re.UNICODE)
    _UMBRAL_PALABRAS = 2  # mensaje de ≤2 palabras se considera corto
    _VENTANA_TURNOS = 3   # 3 mensajes vacíos seguidos = racha

    @classmethod
    def es_mensaje_vacio(cls, mensaje: str) -> bool:
        """True si el mensaje no aporta intención: solo signos, palabra de
        relleno, o frase corta hecha solo de palabras vacías."""
        if not mensaje:
            return True
        texto = mensaje.strip()
        if not texto:
            return True
        if cls._SOLO_PUNTUACION.match(texto):
            return True
        palabras = [p.lower() for p in cls._RX_PALABRA.findall(texto)]
        if not palabras:
            return True
        if len(palabras) > cls._UMBRAL_PALABRAS:
            return False
        return all(p in cls._PALABRAS_VACIAS for p in palabras)

    @classmethod
    def hay_racha(cls, historial_user: list[str], mensaje_actual: str) -> bool:
        """True si los últimos `_VENTANA_TURNOS` mensajes (incluido el
        actual) son todos vacíos."""
        if not cls.es_mensaje_vacio(mensaje_actual):
            return False
        ventana_previos = list(historial_user[-(cls._VENTANA_TURNOS - 1):])
        if len(ventana_previos) < cls._VENTANA_TURNOS - 1:
            return False
        return all(cls.es_mensaje_vacio(m) for m in ventana_previos)

    @classmethod
    def umbral_racha(cls) -> int:
        return cls._VENTANA_TURNOS

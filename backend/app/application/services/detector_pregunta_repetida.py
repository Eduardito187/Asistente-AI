from __future__ import annotations

import re


class DetectorPreguntaRepetida:
    """Detecta cuando el cliente repite la misma pregunta o formulación.

    Si el mensaje actual tiene alta similitud (Jaccard ≥ `_UMBRAL_SIMILITUD`)
    con cualquiera de los últimos `_VENTANA` mensajes del cliente — y el
    actual tiene al menos `_MIN_TOKENS` tokens significativos — el cliente
    está confundido o sintió que no le respondieron. El bloque de contexto
    pide al LLM (1) reconocer la repetición, (2) responder más simple y
    directo, (3) NO listar productos nuevos, (4) ofrecer ayuda más
    específica."""

    _VENTANA = 4
    _UMBRAL_SIMILITUD = 0.6
    _MIN_TOKENS = 3
    _RX_TOKEN = re.compile(r"\b\w{3,}\b", re.UNICODE)
    # Stopwords es-bo / chat — no aportan a la similitud semántica
    _STOPWORDS = frozenset({
        "que", "qué", "cual", "cuál", "como", "cómo", "donde", "dónde",
        "para", "por", "con", "sin", "una", "uno", "del", "los", "las",
        "este", "esta", "esto", "ese", "esa", "eso", "tienes", "tiene",
        "hay", "hace", "puede", "puedo", "quiero", "buscar", "busco",
        "esta", "estoy", "muy", "mas", "más", "menos", "algo", "alguna",
        "algun", "algún", "todos", "todas", "ahora", "tambien", "también",
        "solo", "sólo", "porque", "pero", "aunque", "mientras",
    })

    @classmethod
    def es_repetida(cls, mensaje_actual: str, mensajes_user_previos: list[str]) -> bool:
        if not mensaje_actual or not mensajes_user_previos:
            return False
        tokens_actual = cls._tokens_significativos(mensaje_actual)
        if len(tokens_actual) < cls._MIN_TOKENS:
            return False
        ventana = mensajes_user_previos[-cls._VENTANA:]
        for previo in ventana:
            tokens_previo = cls._tokens_significativos(previo)
            if len(tokens_previo) < cls._MIN_TOKENS:
                continue
            if cls._jaccard(tokens_actual, tokens_previo) >= cls._UMBRAL_SIMILITUD:
                return True
        return False

    @classmethod
    def _tokens_significativos(cls, texto: str) -> set[str]:
        return {
            t.lower()
            for t in cls._RX_TOKEN.findall(texto or "")
            if t.lower() not in cls._STOPWORDS
        }

    @staticmethod
    def _jaccard(a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        inter = len(a & b)
        union = len(a | b)
        return inter / union if union else 0.0

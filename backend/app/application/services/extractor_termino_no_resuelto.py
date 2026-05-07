from __future__ import annotations

import re


class ExtractorTerminoNoResuelto:
    """SRP: extraer el sustantivo candidato a sinonimo del mensaje del cliente.

    Cuando el resolver no resolvio y la busqueda no encontro nada, este
    extractor saca la palabra mas larga (>=4 chars, no stopword) que parezca
    un sustantivo. Esa palabra se registra en synonyms_candidatos."""

    _STOPWORDS = frozenset({
        "para", "necesito", "busco", "quiero", "tengo", "mira", "dame", "podes",
        "puedo", "tienes", "tienen", "este", "esta", "estos", "esas", "estas",
        "como", "cuando", "donde", "cuanto", "cuanta", "siempre", "nunca",
        "presupuesto", "precio", "barato", "caro", "marca", "modelo",
        "ahora", "luego", "tambien", "solo", "todo", "todos", "varias",
        "porque", "entonces", "hola", "buenos", "buenas", "gracias",
        "alguno", "alguna", "muchas", "mucho", "mucha", "muchos",
        "tipo", "color", "anio", "anios", "esperando", "ayuda",
    })

    _RX_TOKEN = re.compile(r"\b([a-zA-ZÀ-ſ]{4,20})\b")

    @classmethod
    def extraer(cls, mensaje: str) -> str | None:
        if not mensaje:
            return None
        candidatos = [
            tok.lower() for tok in cls._RX_TOKEN.findall(mensaje)
            if tok.lower() not in cls._STOPWORDS
        ]
        if not candidatos:
            return None
        # Prefiero el mas largo: usualmente es el sustantivo principal.
        return max(candidatos, key=len)

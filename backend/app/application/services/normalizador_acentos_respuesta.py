from __future__ import annotations

import re


class NormalizadorAcentosRespuesta:
    """SRP: post-procesar la respuesta del LLM para corregir palabras frecuentes
    sin tilde ('mas', 'catalogo', 'tambien') a su forma correcta. NO toca
    voseo ('contame'/'queres') ni nombres propios.

    Aplica solo a palabras del lexico estatico — no inventa acentos."""

    _CORRECCIONES: dict[str, str] = {
        # adverbios y conectores
        r"\bmas\b": "más",
        r"\btambien\b": "también",
        r"\baqui\b": "aquí",
        r"\bahi\b": "ahí",
        r"\bahora\b": "ahora",  # sin acento
        r"\bdespues\b": "después",
        r"\bquiza\b": "quizá",
        r"\bsegun\b": "según",
        r"\basi\b": "así",
        # productos / tecnologia
        r"\bcatalogo\b": "catálogo",
        r"\btecnico\b": "técnico",
        r"\btecnica\b": "técnica",
        r"\bcamara\b": "cámara",
        r"\bbateria\b": "batería",
        r"\bgrafica\b": "gráfica",
        r"\binformatica\b": "informática",
        r"\belectrico\b": "eléctrico",
        r"\belectrica\b": "eléctrica",
        # sustantivos comunes
        r"\bcomputo\b": "cómputo",
        r"\bdiseno\b": "diseño",
        r"\bingenieria\b": "ingeniería",
        r"\barquitectura\b": "arquitectura",
        r"\buniversidad\b": "universidad",
        r"\bautomatico\b": "automático",
        r"\bautomatica\b": "automática",
        r"\bgarantia\b": "garantía",
        r"\bmusica\b": "música",
        r"\bnumero\b": "número",
        r"\bproximo\b": "próximo",
        r"\bproxima\b": "próxima",
        # otros
        r"\bdesicion\b": "decisión",
        r"\bdecision\b": "decisión",
        r"\bopcion\b": "opción",
        r"\bopciones\b": "opciones",
        r"\bbasico\b": "básico",
        r"\bbasica\b": "básica",
    }

    _PATRONES = [(re.compile(rx, re.IGNORECASE), repl) for rx, repl in _CORRECCIONES.items()]

    @classmethod
    def normalizar(cls, texto: str) -> str:
        if not texto:
            return texto
        out = texto
        for patron, reemplazo in cls._PATRONES:
            out = patron.sub(lambda m, r=reemplazo: cls._preservar_caja(m.group(0), r), out)
        return out

    @staticmethod
    def _preservar_caja(original: str, reemplazo: str) -> str:
        if original.isupper():
            return reemplazo.upper()
        if original[0].isupper():
            return reemplazo[0].upper() + reemplazo[1:]
        return reemplazo

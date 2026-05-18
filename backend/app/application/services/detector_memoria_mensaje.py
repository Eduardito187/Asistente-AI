from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MemoriaMensaje:
    texto_recordar: str   # la parte que el cliente quiere guardar
    es_olvido: bool       # True si pide olvidar algo (no recuerdar)


_RX_RECUERDA = re.compile(
    r"(?:"
    r"recuerda\s+que\b"
    r"|recuerda\s+esto\b"
    r"|no\s+olvides\s+que\b"
    r"|no\s+te\s+olvides\s+que\b"
    r"|ten\s+en\s+cuenta\s+que\b"
    r"|tene\s+en\s+cuenta\s+que\b"
    r"|ten\s+en\s+cuenta:\s*"
    r"|anota\s+que\b"
    r"|anotate\s+que\b"
    r"|guardalo\s+que\b"
    r"|guarda\s+que\b"
    r"|acuerdate\s+que\b"
    r"|acuérdate\s+que\b"
    r"|ya\s+te\s+dije\s+que\b"
    r"|ya\s+te\s+dije:\s*"
    r"|es\s+importante\s+que\s+sepas\s+que\b"
    r"|importante:\s*"
    r")",
    re.IGNORECASE,
)

_RX_OLVIDA = re.compile(
    r"(?:"
    r"olvida\s+(?:eso|lo\s+que\s+dije|eso\s+que\s+dije|todo|lo\s+anterior)\b"
    r"|olvidalo\b"
    r"|borra\s+(?:eso|lo\s+que\s+dije)\b"
    r"|no\s+recuerdes\s+(?:eso|lo\s+que\s+dije)\b"
    r")",
    re.IGNORECASE,
)

# Palabras que indican seguimiento de preguntas, no instrucciones de memoria
_RX_FALSO_POSITIVO = re.compile(
    r"recuerda(?:s)?\s+(?:si|cuando|el|la|lo|que\s+(?:te\s+)?mostr|cuánto|cuando)",
    re.IGNORECASE,
)


class DetectorMemoriaMensaje:
    """SRP: detecta si el mensaje es una instrucción de memoria al agente.

    Casos cubiertos:
      "recuerda que tengo presupuesto de 5000" → memorizar hecho
      "no olvides que prefiero Samsung"        → memorizar hecho
      "olvida lo que dije sobre el presupuesto" → instrucción de olvido
      "recuerdas el A35 que me mostraste?"     → NO (es pregunta al agente)
    """

    @classmethod
    def detectar(cls, mensaje: str) -> MemoriaMensaje | None:
        texto = (mensaje or "").strip()
        if not texto:
            return None

        # Olvido explícito
        if _RX_OLVIDA.search(texto):
            return MemoriaMensaje(texto_recordar="", es_olvido=True)

        # Falso positivo: pregunta al agente sobre su memoria
        if _RX_FALSO_POSITIVO.search(texto):
            return None

        m = _RX_RECUERDA.search(texto)
        if not m:
            return None

        # Extraer la parte DESPUÉS del trigger
        resto = texto[m.end():].strip().rstrip(".,;:!?")
        if not resto or len(resto) < 4:
            return None

        return MemoriaMensaje(texto_recordar=resto, es_olvido=False)

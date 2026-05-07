from __future__ import annotations

import re


class DetectorIndecision:
    """Detecta cuando el cliente está indeciso y necesita guía decisiva.

    Casos típicos:
    - "no sé cuál escoger" / "ayúdame a decidir" / "no me decido"
    - "estoy entre X y Y" / "me da igual" / "elegí vos"
    - "cuál me conviene" / "qué me recomendás" sin contexto comparativo

    Este detector NO corta el flujo — alimenta un bloque al system prompt
    para que el LLM responda en MODO DECISIVO: elige uno con justificación,
    no abre listas nuevas, no ofrece más alternativas."""

    _RX = re.compile(
        r"(?:"
        # No puedo decidir
        r"\bno\s+(?:s[ée]|me\s+)?(?:s[ée]\s+)?cu[áa]l\s+(?:elegir|escoger|llevar|comprar)"
        r"|\bno\s+s[ée]\s+(?:qu[ée]|cu[áa]l)\b"
        r"|\bno\s+me\s+(?:puedo\s+)?decid[oi]r?"
        r"|\bestoy\s+indecis[oa]\b"
        r"|\bme\s+(?:cuesta|es\s+dif[ií]cil)\s+decidir"
        r"|\bayud[áa](?:me)?\s+a\s+(?:decidir|elegir|escoger)"
        # Estoy entre X y Y
        r"|\bestoy\s+(?:entre|dudando\s+entre)"
        r"|\bdud[oa]\s+entre\b"
        r"|\bno\s+s[ée]\s+entre\b"
        # Pide elección
        r"|\beleg[íi]\s+(?:vos|tu|por\s+m[íi])\b"
        r"|\b(?:qu[ée]|cu[áa]l)\s+\w*\s*(?:eleg[íi]r[ií]as|tomar[íi]as|comprar[íi]as|"
        r"llevar[ií]as|pidir[ií]as|recomendar[íi]as)"
        r"|\b(?:eleg[íi]r[ií]as|tomar[íi]as|comprar[íi]as|llevar[ií]as)\s+(?:vos|tu)\b"
        r"|\bsi\s+fuera(?:s)?\s+(?:tuyo|por\s+ti|por\s+vos)"
        r"|\bdame\s+(?:el\s+)?(?:ganador|tu\s+elecci[óo]n)"
        r"|\bcu[áa]l\s+(?:te\s+)?(?:ser[ií]a|fuera)\s+tu\s+(?:elecci[óo]n|favorit[oa])"
        # Cliente declara igualdad
        r"|\bme\s+da\s+(?:igual|lo\s+mismo)"
        r"|\bno\s+me\s+importa\s+cu[áa]l"
        r"|\btodos?\s+me\s+gustan?"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def es_indeciso(cls, mensaje: str) -> bool:
        if not mensaje:
            return False
        return bool(cls._RX.search(mensaje))

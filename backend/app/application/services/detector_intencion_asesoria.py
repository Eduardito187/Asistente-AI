from __future__ import annotations

import re


class DetectorIntencionAsesoria:
    """Detecta cuando el cliente pide asesoria en lugar de buscar algo puntual.

    Gatilla 'modo asesor' en frases tipicas de consulta abierta:
      - 'cual me conviene', 'que me recomienda', 'asesorame', 'ayudame a elegir'
      - 'no se cual llevar', 'no me interesa la marca', 'me da igual'
      - 'es mi primera laptop', 'soy nuevo en esto', 'no entiendo de TVs'

    En modo asesor el agente debe hacer 1-3 preguntas de perfilado antes
    de recomendar, y luego presentar la plantilla (opcion principal +
    alternativas + razon + pregunta de cierre). Cuando el modo NO esta
    activo se asume busqueda concreta y se responde directo.

    El detector es deterministico y solo usa regex — no depende del LLM."""

    _RX_ASESORIA = re.compile(
        r"\b(?:"
        r"cual(?:es)?\s+me\s+(?:conviene|recomienda|sugiere|serviria|quedaria|iria)"
        r"|que\s+me\s+(?:recomienda|sugiere|aconseja|conviene)"
        r"|cual\s+(?:es\s+)?(?:la\s+)?(?:mejor|mas\s+recomendable|mas\s+conveniente|mas\s+completa|top)"
        r"|asesor(?:ame|arme|ar|ate|eme|e|a)"
        r"|aconseja(?:me|rme|r)?"
        r"|ayuda(?:me|rme)?\s+a\s+(?:elegir|decidir|escoger)"
        r"|no\s+se\s+(?:cual|que|por\s+donde|bien|mucho)"
        r"|no\s+me\s+(?:interesa|importa|convence)\s+(?:la\s+)?marca"
        r"|me\s+da\s+(?:igual|lo\s+mismo)"
        r"|primera\s+(?:laptop|tv|televisor|celular|compra)"
        r"|primer\s+(?:celular|laptop|televisor|tv)"
        r"|soy\s+nuevo"
        r"|que\s+opin(?:a|as)"
        r"|que\s+(?:tal|piensa|crees)\s+(?:es|seria)"
        r"|orient(?:ame|arme|acion|a)"
        r"|guia(?:me|rme|r)?"
        r"|decid(?:i|ite|ime)\s+(?:vos|tu|usted)"
        r"|elegi(?:me|r)?\s+(?:vos|tu|usted|uno)"
        r"|dime\s+cual"
        r"|no\s+entiendo\s+(?:de|mucho)"
        r"|estoy\s+(?:perdido|confundid[oa]|entre)"
        r")\b",
        re.IGNORECASE,
    )

    _RX_MARCA_INDIFERENTE = re.compile(
        r"\b(?:"
        r"no\s+me\s+(?:interesa|importa)\s+(?:la\s+)?marca"
        r"|(?:la\s+)?marca\s+(?:no\s+(?:me\s+)?(?:importa|interesa)|me\s+da\s+igual)"
        r"|cualquier\s+marca"
        r"|sin\s+marca\s+preferida"
        r"|marca\s+indiferente"
        r")\b",
        re.IGNORECASE,
    )

    @classmethod
    def es_modo_asesor(cls, texto: str) -> bool:
        if not texto:
            return False
        return bool(cls._RX_ASESORIA.search(texto))

    @classmethod
    def marca_es_indiferente(cls, texto: str) -> bool:
        if not texto:
            return False
        return bool(cls._RX_MARCA_INDIFERENTE.search(texto))

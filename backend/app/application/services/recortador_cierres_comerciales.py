from __future__ import annotations

import re

from .clasificador_etapa_conversacional import EtapaConversacional


class RecortadorCierresComerciales:
    """SRP: elimina cierres tipo "¿querés que te lo agregue al carrito?"
    cuando la etapa no es de decisión/compra. La plantilla repetida en cada
    turno cansa al cliente y rompe la regla 5/6 del prompt.

    Se ejecuta post-LLM, sobre la respuesta final. Solo recorta la ÚLTIMA
    oración si es un cierre plantilla; no toca preguntas legítimas del
    medio del texto ("¿Qué presupuesto tenés?" está bien, "¿Te lo agrego
    al carrito?" al final en etapa exploración no).
    """

    _ETAPAS_PERMITIDAS = frozenset({
        EtapaConversacional.DECISION,
        EtapaConversacional.COMPRA,
    })

    _RX_CIERRE_CARRITO = re.compile(
        r"(?:^|[\n\.\?!])\s*["
        r"¿¡\-\*\s]*"
        r"(?:"
        r"[¿¡]?(?:quer[eé]s|quieres|te\s+sirve|te\s+gusta|te\s+conviene|"
        r"te\s+interesa|te\s+animas|te\s+anim[aá]s|te\s+lo\s+llevo|"
        r"lo\s+agregamos|agregamos|lo\s+agrego|te\s+lo\s+agrego|"
        r"te\s+lo\s+reservo|vamos\s+al\s+carrito)"
        r"[^\n\.\?!]*"
        r"(?:carrito|reserv|llevo|llevar|comprar|compra|elegir|probamos|"
        r"agreg(?:o|ar|amos|ame))"
        r"[^\n\.\?!]*[\?\!\.]+"
        r")\s*$",
        re.IGNORECASE | re.DOTALL,
    )

    _RX_SERVIR_AL_FINAL = re.compile(
        r"(?:^|[\n\.\?!])\s*[¿¡\-\*\s]*"
        r"[¿¡]?te\s+sirve\s+algun[oa][^\n\?]*\?+[^\n]*$",
        re.IGNORECASE,
    )

    @classmethod
    def recortar(cls, respuesta: str, etapa: EtapaConversacional) -> str:
        if not respuesta or etapa in cls._ETAPAS_PERMITIDAS:
            return respuesta
        texto = respuesta
        for rx in (cls._RX_CIERRE_CARRITO, cls._RX_SERVIR_AL_FINAL):
            texto = rx.sub("", texto).rstrip()
        return texto or respuesta

from __future__ import annotations

import re


class DetectorAsesoriaMostrados:
    """SRP: detecta cuando el cliente pide asesoría/comparación REFERENCIADA
    a los productos mostrados en el turno anterior. No extrae SKUs; solo
    clasifica la intención para que el caller (procesar_chat_service) dispare
    comparar_productos sobre `perfil.ultimos_skus_mostrados`.

    Ejemplos que disparan:
      - "ayudame a decidir"
      - "ayudame a elegir entre los modelos"
      - "cual me conviene"
      - "cual es el mejor"
      - "comparame los"
      - "cual es mejor entre los que me mostraste"
      - "no se cual elegir"
      - "que me recomiendas"
    """

    _RX_ASESORIA = re.compile(
        r"\b(?:"
        r"ayuda(?:me|)\s+a\s+(?:decidir|elegir|escoger)|"
        r"cu[aá]l\s+me\s+conviene|"
        r"cu[aá]l\s+(?:es\s+)?(?:el|la)\s+mejor|"
        r"cu[aá]l\s+(?:es\s+)?mejor(?:\s+entre)?|"
        r"compar(?:a|ame|alos|alas|amelos|amelas|amos|amoslos)|"
        r"no\s+s[eé]\s+cu[aá]l\s+(?:elegir|escoger|decidir)|"
        r"qu[eé]\s+me\s+recomend[áa]s|qu[eé]\s+recomend[áa]s|"
        r"qu[eé]\s+me\s+ofrec[eé]s|"
        r"me\s+ayud[áa]s\s+a\s+(?:decidir|elegir)"
        r")\b",
        re.IGNORECASE,
    )

    @classmethod
    def es_asesoria_sobre_mostrados(cls, mensaje: str | None) -> bool:
        if not mensaje:
            return False
        return bool(cls._RX_ASESORIA.search(mensaje))

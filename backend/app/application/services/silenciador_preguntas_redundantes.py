from __future__ import annotations

import re


class SilenciadorPreguntasRedundantes:
    """SRP: recorta preguntas del LLM sobre slots que el cliente YA declaró
    en `perfil_sesion`. Implementa la regla 7 del prompt ("no re-preguntar lo
    ya dicho") como filtro de salida. Opera oración por oración: detecta
    patrones de pregunta sobre marca/presupuesto/género/pulgadas y los
    elimina cuando el slot correspondiente del perfil ya está poblado.
    """

    _PATRONES: tuple[tuple[re.Pattern[str], str], ...] = (
        (
            re.compile(
                r"[¿\?]?\s*(?:tenes|ten[eé]s|tienes|hay)\s+alguna\s+marca"
                r"[^\.\?\!\n]*[\.\?\!]*",
                re.IGNORECASE,
            ),
            "marca_preferida",
        ),
        (
            re.compile(
                r"[¿\?]?\s*(?:que|qu[eé])\s+marca\s+(?:prefer[ií]s|te\s+gusta|"
                r"te\s+interesa|queres|quieres|ten[eé]s\s+en\s+mente)"
                r"[^\.\?\!\n]*[\.\?\!]*",
                re.IGNORECASE,
            ),
            "marca_preferida",
        ),
        (
            re.compile(
                r"[¿\?]?\s*(?:cu[aá]l|que|qu[eé])\s+es\s+tu\s+presupuesto"
                r"[^\.\?\!\n]*[\.\?\!]*",
                re.IGNORECASE,
            ),
            "presupuesto_max",
        ),
        (
            re.compile(
                r"[¿\?]?\s*(?:tenes|ten[eé]s|tienes)\s+(?:un\s+)?presupuesto"
                r"[^\.\?\!\n]*[\.\?\!]*",
                re.IGNORECASE,
            ),
            "presupuesto_max",
        ),
        (
            re.compile(
                r"[¿\?]?\s*(?:cu[aá]nto\s+(?:pens[aá]s|quer[eé]s)\s+gastar|"
                r"hasta\s+cu[aá]nto\s+(?:quer[eé]s|pod[eé]s)\s+(?:gastar|invertir)|"
                r"qu[eé]\s+rango\s+de\s+precio[^\?\.\!\n]*)"
                r"[^\.\?\!\n]*[\.\?\!]*",
                re.IGNORECASE,
            ),
            "presupuesto_max",
        ),
        (
            re.compile(
                r"[¿\?]?\s*(?:es|ser[ií]a)\s+para\s+(?:un\s+)?(?:hombre|mujer|nino|nina|chico|chica|dama|caballero)"
                r"[^\.\?\!\n]*[\.\?\!]*",
                re.IGNORECASE,
            ),
            "genero_declarado",
        ),
        (
            re.compile(
                r"[¿\?]?\s*(?:qu[eé]|que)\s+(?:tama[nñ]o|pulgadas)\s+"
                r"(?:prefer[ií]s|te\s+interesa|quer[eé]s|buscas)"
                r"[^\.\?\!\n]*[\.\?\!]*",
                re.IGNORECASE,
            ),
            "pulgadas",
        ),
        (
            re.compile(
                r"[¿\?]?\s*(?:para\s+qu[eé]\s+(?:vas|v[aá]s|lo)\s+a?\s*usar|"
                r"qu[eé]\s+uso\s+le\s+vas\s+a\s+dar|"
                r"qu[eé]\s+uso\s+le\s+(?:dar[ií]as|das)|"
                r"es\s+para\s+(?:trabajo|estudio|gaming|jugar|la\s+u|la\s+facu|la\s+escuela)|"
                r"(?:para\s+qu[eé]|qu[eé]\s+uso)\s+(?:la|lo|la\s+vas|lo\s+vas)\s+(?:a\s+usar|usar[ií]as))"
                r"[^\.\?\!\n]*[\.\?\!]*",
                re.IGNORECASE,
            ),
            "uso_declarado",
        ),
        (
            re.compile(
                r"[¿\?]?\s*(?:qu[eé]\s+tipo\s+de\s+"
                r"(?:lavadora|secadora|refrigerador|refri|cocina|microondas|aire\s+acondicionado|"
                r"tv|tele|televisi[oó]n|monitor|laptop|celular|tel[eé]fono)"
                r"\s+(?:prefer[ií]s|buscas|quer[eé]s|te\s+interesa|ten[eé]s\s+en\s+mente)|"
                r"qu[eé]\s+tipo\s+(?:prefer[ií]s|buscas|quer[eé]s|te\s+interesa))"
                r"[^\.\?\!\n]*[\.\?\!]*",
                re.IGNORECASE,
            ),
            "subcategoria_foco",
        ),
        (
            re.compile(
                r"[¿\?]?\s*(?:de\s+qu[eé]\s+ciudad\s+(?:sos|eres|est[aá]s|venís)|"
                r"en\s+qu[eé]\s+ciudad\s+(?:est[aá]s|sos|viv[ií]s|vives|te\s+encontr[aá]s)|"
                r"(?:cu[aá]l\s+es\s+tu\s+ciudad|de\s+d[oó]nde\s+sos|de\s+d[oó]nde\s+eres))"
                r"[^\.\?\!\n]*[\.\?\!]*",
                re.IGNORECASE,
            ),
            "ciudad_sesion",
        ),
    )

    @classmethod
    def silenciar(cls, respuesta: str, perfil) -> str:
        if not respuesta or perfil is None:
            return respuesta
        texto = respuesta
        for patron, slot in cls._PATRONES:
            if cls._slot_lleno(perfil, slot):
                texto = patron.sub("", texto)
        return cls._limpiar_vacios(texto).strip() or respuesta

    @staticmethod
    def _slot_lleno(perfil, slot: str) -> bool:
        valor = getattr(perfil, slot, None)
        if valor is None:
            return False
        if isinstance(valor, str):
            return bool(valor.strip())
        return bool(valor)

    @staticmethod
    def _limpiar_vacios(texto: str) -> str:
        """Colapsa blancos múltiples dejados por los stripes. No inserta
        contenido nuevo — solo elimina runs de espacios/saltos."""
        texto = re.sub(r"[ \t]+\n", "\n", texto)
        texto = re.sub(r"\n{3,}", "\n\n", texto)
        texto = re.sub(r"[ \t]{2,}", " ", texto)
        return texto

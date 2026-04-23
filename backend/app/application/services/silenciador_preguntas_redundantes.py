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

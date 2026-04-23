from __future__ import annotations

import re


class BloqueadorListaRepetida:
    """SRP: detecta cuando la respuesta del agente lista los mismos SKUs que
    ya se mostraron en turnos anteriores aunque el cliente haya pedido
    'otra opción / distinta / más opciones'. Permite al chat service
    re-ejecutar la búsqueda excluyendo los SKUs mostrados.

    Esta es la queja histórica más frecuente: 'me repite los mismos'."""

    _RX_FOLLOWUP = re.compile(
        r"\b("
        r"otra|otro|otras|otros|"
        r"distint[ao]s?|diferent[ae]s?|"
        r"mas\s+opciones?|mas\s+modelos?|mas\s+alternativas?|"
        r"muestra(?:me)?\s+(?:mas|otr[ao])|"
        r"dame\s+(?:mas|otra|otro)|"
        r"alternativa[s]?"
        r")\b",
        re.IGNORECASE,
    )

    @classmethod
    def es_follow_up_de_repeticion(cls, mensaje: str | None) -> bool:
        """True cuando el mensaje del cliente pide variar respecto al listado
        previo (y por lo tanto repetir los SKUs seria bug)."""
        if not mensaje:
            return False
        return bool(cls._RX_FOLLOWUP.search(mensaje))

    @staticmethod
    def lista_repetida(
        skus_nuevos: list[str], ultimos_mostrados: set[str]
    ) -> bool:
        """True si todos los SKUs citados en la respuesta actual ya estaban
        en el listado anterior. Si agregó al menos uno nuevo, no es repetida."""
        if not skus_nuevos or not ultimos_mostrados:
            return False
        return all(s in ultimos_mostrados for s in skus_nuevos)

    @staticmethod
    def skus_del_perfil(ultimos_skus_mostrados: str | None) -> set[str]:
        """Parsea el campo `perfiles_sesion.ultimos_skus_mostrados` (CSV)."""
        if not ultimos_skus_mostrados:
            return set()
        return {s.strip() for s in ultimos_skus_mostrados.split(",") if s.strip()}

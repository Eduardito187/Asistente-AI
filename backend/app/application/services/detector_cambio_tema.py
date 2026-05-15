from __future__ import annotations

import re


class DetectorCambiaTema:

    _PATRON_OLVIDA = re.compile(
        r"\b(olvida(me|te|r)?\s+(eso|lo\s+anterior|todo\s+eso)|espera[,\s]+olvida|para[,\s]+olvida)",
        re.IGNORECASE,
    )

    _PATRON_MEJOR_BUSQUEDA = re.compile(
        r"\bmejor\s+(busca|muéstrame|muestrame|quiero|dame|consígueme|consigueme|necesito)\b",
        re.IGNORECASE,
    )

    _PATRON_CAMBIO_OPINION = re.compile(
        r"\b(me\s+cambié\s+de\s+(idea|opinión|opinion)|cambié\s+de\s+(idea|opinión|opinion))\b",
        re.IGNORECASE,
    )

    _PATRON_YA_NO = re.compile(
        r"\bya\s+no\s+(quiero|me\s+interesa|busco|necesito)\s+(eso|esa|ese|esto|esto\s+que)?\b",
        re.IGNORECASE,
    )

    _PATRON_EN_REALIDAD = re.compile(
        r"\ben\s+realidad\s+(quiero|busco|necesito|me\s+interesa)\b",
        re.IGNORECASE,
    )

    _PATRON_NADA_QUE_VER = re.compile(
        r"\bnada\s+que\s+ver[,\s]+(quiero|busco|necesito)\b",
        re.IGNORECASE,
    )

    _PATRON_NO_MEJOR = re.compile(
        r"\bno[,\s]+mejor\s+(quiero|busco|necesito|dame|muéstrame|muestrame)\b",
        re.IGNORECASE,
    )

    _PATRON_BOLIVIANO = re.compile(
        r"\b(al\s+final\s+mejor\s+(quiero|busco|necesito|dame)|"
        r"mejor\s+dicho\s+(quiero|busco|necesito)|"
        r"qué\s+tal\s+si\s+mejor\s+(busco|quiero|vemos)|"
        r"que\s+tal\s+si\s+mejor\s+(busco|quiero|vemos))\b",
        re.IGNORECASE,
    )

    _FALSO_POSITIVO = re.compile(
        r"\bmejor\s+(precio|calidad|marca|opcion|opción|alternativa|rendimiento|desempeño)\b",
        re.IGNORECASE,
    )

    @classmethod
    def es_cambio_tema(cls, mensaje: str) -> bool:
        if cls._FALSO_POSITIVO.search(mensaje):
            return False
        return bool(
            cls._PATRON_OLVIDA.search(mensaje)
            or cls._PATRON_MEJOR_BUSQUEDA.search(mensaje)
            or cls._PATRON_CAMBIO_OPINION.search(mensaje)
            or cls._PATRON_YA_NO.search(mensaje)
            or cls._PATRON_EN_REALIDAD.search(mensaje)
            or cls._PATRON_NADA_QUE_VER.search(mensaje)
            or cls._PATRON_NO_MEJOR.search(mensaje)
            or cls._PATRON_BOLIVIANO.search(mensaje)
        )

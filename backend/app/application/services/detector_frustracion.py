from __future__ import annotations

import re


class DetectorFrustracion:
    """Detecta señales de frustración del cliente para derivarlo a ventas
    telefónicas (canal humano).

    Dos niveles que disparan derivación:
    - ALTO: una sola señal fuerte basta. Cliente pide explícitamente humano,
      insulta al bot, o niega su utilidad ("no sirves").
    - MEDIO: dos o más señales blandas en el mismo mensaje (no me ayudas,
      no me entiendes, repetí, perdiendo tiempo, harto, gritos en
      mayúsculas, exclamaciones múltiples).

    Es deterministico — no consulta LLM. La idea es cortar antes de gastar
    tokens cuando el cliente ya se cansó de hablar con un bot."""

    # ===== ALTO — una señal basta para derivar ==============================

    _RX_PIDE_HUMANO = re.compile(
        r"(?:"
        r"\bhablar\s+con\s+(?:un[ao]?|al?gun[ao]?|alguien|persona|humano|"
        r"operador[ae]?|agente|asesor[ae]?|ejecutiv[oa]|vendedor[ae]?|"
        r"encargad[oa]|representante)"
        r"|\bp[áa]same\s+con\b"
        r"|\bcomun[ií]came\s+con\b"
        r"|\bcomuni(?:que|car)\w*\s+con\b"
        r"|\b(?:cont[áa]ctame|contactarme|contactar|contacto)\s+(?:con|a|al)\s+"
        r"(?:un[ao]?|alguien|asesor|humano|persona|vendedor|ventas|soporte|"
        r"agente|operador|atenci[óo]n)"
        r"|\bc[óo]mo\s+(?:me\s+)?(?:contacto|comunico|llamo|hablo)\s+(?:con|a|al)"
        r"|\bquiero\s+(?:hablar\s+con|que\s+me\s+atienda)\s+(?:un[ao]?|alguien|"
        r"persona|humano|operador|asesor|vendedor|ejecutivo)"
        r"|\bnecesito\s+(?:un[ao]?|hablar\s+con|el\s+|un\s+|tu\s+)?"
        r"(?:humano|persona\s+real|asesor|operador|vendedor|"
        r"tel[ée]fono|whatsapp|n[úu]mero|contacto)"
        r"|\bdame\s+(?:el\s+|un\s+|tu\s+)?(?:tel[ée]fono|whatsapp|n[úu]mero|"
        r"contacto)"
        r"|\bp[áa]sa(?:me)?\s+(?:el\s+|un\s+|tu\s+)?(?:tel[ée]fono|whatsapp|n[úu]mero)"
        r"|\bme\s+das?\s+(?:el\s+|un\s+|tu\s+)?(?:tel[ée]fono|whatsapp|n[úu]mero|"
        r"contacto)"
        r"|\batenci[óo]n\s+humana\b"
        r"|\bagente\s+humano\b"
        r"|\bpersona\s+(?:de\s+)?verdad\b"
        r"|\balguien\s+real\b"
        r"|\bno\s+(?:un|al)\s+bot\b"
        r"|\bno\s+quiero\s+(?:hablar\s+con\s+)?(?:el\s+)?bot\b"
        r"|\bod(?:io|i[oa]ba)\s+(?:hablar\s+con\s+)?bots?\b"
        r"|\bn[uú]mero\s+(?:de\s+)?(?:tel[ée]fono|whatsapp|contacto|atenci[óo]n|"
        r"ventas|soporte)"
        r"|\btel[ée]fono\s+(?:de|para)\s+(?:atenci[óo]n|ventas|soporte|contacto|"
        r"hablar)"
        r"|\bwhatsapp\s+(?:de|para)\s+(?:atenci[óo]n|ventas|soporte|contacto)"
        r"|\bllamar\s+a\s+(?:la\s+)?(?:tienda|ventas|soporte|atenci[óo]n)"
        r")",
        re.IGNORECASE,
    )

    _RX_INSULTO_BOT = re.compile(
        r"(?:"
        # ataque directo al bot (eres / sos + adjetivo)
        r"\b(?:eres|sos|er[ae]s)\s+(?:un[ao]?\s+)?(?:in[úu]til|estu?p[íi]d[oa]|"
        r"imb[ée]cil|tont[oa]|p[ée]sim[oa]|terrible|horrible|patetic[oa]|"
        r"in[úu]tile?|basura|porquer[ií]a|asco|asqueros[oa]|nefasta?)"
        # qué + adjetivo dirigido al servicio
        r"|\bqu[ée]\s+(?:porquer[ií]a|asco|basura|mierda|verg[üu]enza|cag[au]da)\s+"
        r"(?:de\s+)?(?:bot|servicio|chat|asistente|sistema)"
        # malas palabras directas (es-bo / latam)
        r"|\bbot\s+(?:de\s+)?(?:mierda|porquer[ií]a)"
        r"|\bque\s+(?:bot|chat|asistente)\s+(?:in[úu]til|tont[oa]|mal[oa])"
        r")",
        re.IGNORECASE,
    )

    _RX_NO_SIRVE_BOT = re.compile(
        r"(?:"
        r"\bno\s+sirves?\b"
        r"|\bno\s+funcion[áa]s?\b"
        r"|\bno\s+sabes\s+nada\b"
        r"|\bpara\s+(?:que|qu[ée])\s+sirves?\b"
        r"|\bno\s+haces\s+nada\s+bien\b"
        r"|\bno\s+entendiste\s+nada\b"
        r")",
        re.IGNORECASE,
    )

    # ===== MEDIO — necesitan 2+ señales en el mismo mensaje =================

    _RX_NO_AYUDA = re.compile(
        r"(?:"
        r"\bno\s+me\s+(?:est[áa]s\s+)?ayud[áa]s?(?:\s+en\s+nada)?\b"
        r"|\bno\s+me\s+(?:est[áa]s\s+)?resol[vué]\w*\b"
        r"|\bno\s+me\s+das?\s+(?:lo\s+que\s+(?:te\s+)?pido|nada)"
        r"|\bno\s+me\s+(?:est[áa]s\s+)?(?:respondiendo|contestando)\s+(?:lo\s+que|bien)"
        r")",
        re.IGNORECASE,
    )

    _RX_NO_ENTIENDE = re.compile(
        r"(?:"
        r"\bno\s+(?:me\s+)?entiend[ae]s\b"
        r"|\bno\s+me\s+(?:est[áa]s\s+)?(?:entendiendo|escuchando)\b"
        r"|\bno\s+capt[áa]s\b"
        r"|\bno\s+pillas\s+lo\s+que\s+(?:te\s+)?digo"
        r")",
        re.IGNORECASE,
    )

    _RX_REPETICION = re.compile(
        r"(?:"
        r"\bya\s+te\s+(?:lo\s+)?(?:dije|expliqu[ée])\b"
        r"|\bte\s+(?:lo\s+)?(?:repito|estoy\s+repitiendo)\b"
        r"|\b(?:por\s+)?(?:tercera|cuarta|quinta|en[ée]sima)\s+vez\b"
        r"|\botra\s+vez\s+(?:lo\s+mismo|con\s+lo\s+mismo)"
        r"|\bcu[áa]ntas\s+veces\s+(?:te\s+)?(?:tengo\s+que\s+)?(?:dec[íi]r|repetir)"
        r"|\bsigues?\s+sin\s+entender"
        r")",
        re.IGNORECASE,
    )

    _RX_PERDIDA_TIEMPO = re.compile(
        r"(?:"
        r"\b(?:que\s+|qu[ée]\s+)?p[ée]rdida\s+de\s+tiempo\b"
        r"|\bestoy\s+perdiendo\s+(?:mi\s+)?tiempo\b"
        r"|\bme\s+est[áa]s?\s+haciendo\s+perder\s+(?:el\s+)?tiempo"
        r"|\bllevo\s+(?:m[áa]s\s+de\s+)?(?:una\s+|media\s+)?(?:hora|horas|rato|"
        r"un\s+rato|d[íi]as?)\s+(?:tratando|intentando|peleando|chateando)"
        r"|\bhace\s+rato\s+(?:que\s+)?(?:te|estoy)"
        r")",
        re.IGNORECASE,
    )

    _RX_HARTO = re.compile(
        r"(?:"
        r"\bestoy\s+(?:hart[oa]|cansad[ao]|aburrid[oa]|fastidiad[oa]|"
        r"frustrad[oa]|estresad[oa]|enojad[oa])\b"
        r"|\bme\s+(?:tenes|tienes|tiene)\s+hart[oa]\b"
        r"|\bme\s+aburre\b"
        r"|\bqu[ée]\s+(?:fastidio|frustracion|frustraci[óo]n|paciencia|barbaridad)"
        r"|\bme\s+(?:est[áa]s\s+)?frustrand[oa]"
        r"|\bes(?:t[oa]y)?\s+desespera\w+\b"
        r")",
        re.IGNORECASE,
    )

    # Caps lock SHOUTING: palabra de 5+ letras en mayúsculas (con tildes
    # españolas). Excluye SKUs típicos (mezclan dígitos) y siglas cortas.
    _RX_SHOUTING = re.compile(r"\b[A-ZÁÉÍÓÚÑÜ]{5,}\b")

    # Múltiples exclamaciones / interrogaciones seguidas: !!! ??? !!?
    _RX_MULTI_PUNTUACION = re.compile(r"[!?]{3,}")

    # ===== API publica ======================================================

    @classmethod
    def debe_derivar(cls, mensaje: str) -> bool:
        """True si el mensaje justifica derivar al canal humano."""
        if not mensaje:
            return False
        if cls._es_alto(mensaje):
            return True
        return cls._cuenta_senales_medias(mensaje) >= 2

    @classmethod
    def nivel(cls, mensaje: str) -> str:
        """Devuelve etiqueta para metricas: 'alto' | 'medio' | 'bajo' | 'ninguno'.
        - alto = cliente pide humano o insulta al bot (derivar)
        - medio = 2+ señales blandas (derivar)
        - bajo = 1 señal blanda (registrar pero seguir)
        - ninguno = sin señal"""
        if not mensaje:
            return "ninguno"
        if cls._es_alto(mensaje):
            return "alto"
        n = cls._cuenta_senales_medias(mensaje)
        if n >= 2:
            return "medio"
        if n == 1:
            return "bajo"
        return "ninguno"

    # ===== Internos =========================================================

    @classmethod
    def _es_alto(cls, mensaje: str) -> bool:
        return bool(
            cls._RX_PIDE_HUMANO.search(mensaje)
            or cls._RX_INSULTO_BOT.search(mensaje)
            or cls._RX_NO_SIRVE_BOT.search(mensaje)
        )

    @classmethod
    def _cuenta_senales_medias(cls, mensaje: str) -> int:
        return sum(
            1 for rx in (
                cls._RX_NO_AYUDA,
                cls._RX_NO_ENTIENDE,
                cls._RX_REPETICION,
                cls._RX_PERDIDA_TIEMPO,
                cls._RX_HARTO,
                cls._RX_SHOUTING,
                cls._RX_MULTI_PUNTUACION,
            ) if rx.search(mensaje)
        )

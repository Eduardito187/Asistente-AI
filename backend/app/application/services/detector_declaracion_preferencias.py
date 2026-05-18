from __future__ import annotations

import re


class DetectorDeclaracionPreferencias:
    """Detecta mensajes que son SOLO declaracion de preferencias/filtros sin
    verbo de pedido explicito.

    Ejemplo tipico (el que fallo): 'marca samsung, presupuesto 6000bs'
    El LLM confunde ese mensaje como solicitud de detalle del producto previo
    en lugar de una nueva busqueda con filtros.

    Dispara cuando:
    - El mensaje NO tiene verbo de pedido (quiero/busco/dame/muestrame/etc.)
    - El mensaje NO tiene signo de pregunta
    - El mensaje es corto (< 13 tokens)
    - Tiene al menos un atributo filterable:
        * Cualquier atributo tecnico que ExtractorAtributosMensaje detecte
          (ram, ssd, hz, mah, mp, 5g, panel, resolucion, pulgadas, etc.)
        * O una señal de marca/presupuesto/uso/tier (via _RX_EXTRA)

    Cuando dispara, el orquestador ejecuta buscar_productos directo en lugar
    de delegarlo al LLM (que ignora los filtros nuevos)."""

    # Valores de almacenamiento conocidos solos ("256gb", "512gb") — solo
    # usados en el contexto de un mensaje de correccion para no introducir
    # falsos positivos en mensajes generales.
    _SSD_VALIDOS = frozenset([32, 64, 128, 256, 512, 1024, 2048])
    _RX_GB_STANDALONE = re.compile(r"\b(\d{2,4})\s*gb\b", re.IGNORECASE)

    # Señales que ExtractorAtributosMensaje NO cubre pero que son igualmente
    # validas como declaracion de preferencia: marca, presupuesto, uso, tier.
    _RX_EXTRA = re.compile(
        r"\b(?:"
        r"marca\s+\w+"
        r"|presupuesto\s*[\d,.]+"
        r"|hasta\s+\d+\s*(?:bs|bolivianos?|bob)"
        r"|\d+\s*(?:bs|bob)\s+(?:de\s+)?presupuesto"
        r"|para\s+(?:gaming|estudio|trabajo|oficina|diseño|diseno|programar|cocina|exteriores?)"
        r"|tope\s+de\s+gama|gama\s+(?:alta|media|baja)"
        r"|entry[\s-]?level|low[\s-]?end|high[\s-]?end"
        r"|economico|lo\s+mas\s+(?:barato|economico)"
        r"|lo\s+mejor|el\s+mejor"
        r")\b",
        re.IGNORECASE,
    )

    # Verbos que indican pedido explicito — si aparecen, el mensaje NO es
    # solo declaracion de preferencias, el LLM puede manejarlo.
    _RX_PEDIDO_EXPLICITO = re.compile(
        r"\b(?:"
        r"quiero|busco|necesito|dame|muestra(?:me)?|conseguir|comprar|llevar"
        r"|recomienda(?:me)?|sugiere(?:me)?|hay|tienen|tienes|muestrame"
        r"|dame|busca(?:me)?|encuentra(?:me)?|busqueme|listame"
        r")\b",
        re.IGNORECASE,
    )

    # Verbos de correccion/aclaracion — el cliente repite o aclara un
    # atributo que ya menciono antes. Tratamos el mensaje completo como
    # declaracion de preferencia (no como pedido nuevo al LLM).
    _RX_CORRECCION = re.compile(
        r"\b(?:dije|digo|decia|mencion[eé]|puse|pongo|queria|quiero decir|"
        r"repito|o\s+sea|es\s+decir|me\s+refiero)\b",
        re.IGNORECASE,
    )

    @classmethod
    def es_solo_declaracion(cls, mensaje: str) -> bool:
        """True si el mensaje es pura declaracion de preferencias sin pedido
        explicito de producto. Cuando es True, el orquestador debe ejecutar
        buscar_productos directo en lugar de delegarlo al LLM."""
        if not mensaje:
            return False
        # Largo: dejar al LLM
        if len(mensaje.split()) > 12:
            return False
        # Pregunta explicita: dejar al LLM
        if "?" in mensaje:
            return False

        from .extractor_atributos_mensaje import ExtractorAtributosMensaje

        # Mensajes de correccion/aclaracion ("dije 256gb", "decia 8gb de ram"):
        # el cliente esta reforzando un atributo previo — los verbos de
        # correccion NO son verbos de pedido, por eso los tratamos separado.
        es_correccion = bool(cls._RX_CORRECCION.search(mensaje))
        if es_correccion:
            # El extractor cubre la mayoria de casos (RAM, Hz, pulgadas, etc.)
            if ExtractorAtributosMensaje.extraer(mensaje).tiene_alguno():
                return True
            # "dije 256gb" — GB standalone sin keyword de almacenamiento.
            # En contexto de correccion, un valor en _SSD_VALIDOS >= 128 es
            # inequivocamente almacenamiento (RAM valida <= 64).
            m = cls._RX_GB_STANDALONE.search(mensaje)
            if m and int(m.group(1)) in cls._SSD_VALIDOS and int(m.group(1)) >= 128:
                return True
            return False

        # Con verbo de pedido (y sin ser correccion): el LLM puede inferir
        if cls._RX_PEDIDO_EXPLICITO.search(mensaje):
            return False

        # Fuente de verdad primaria: cualquier atributo tecnico detectable
        # (pulgadas, panel, resolucion, RAM, SSD, Hz, mAh, MP, 5G, OS,
        # inverter, no_frost, smart_tv, NFC, USB-C, HDMI, potencia, etc.)
        if ExtractorAtributosMensaje.extraer(mensaje).tiene_alguno():
            return True

        # Señales complementarias: marca/presupuesto/uso/tier no cubiertos
        # por ExtractorAtributosMensaje
        return bool(cls._RX_EXTRA.search(mensaje))

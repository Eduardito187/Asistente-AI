from __future__ import annotations

import re


class DetectorIntentionVaga:
    """SRP: detecta mensajes donde el cliente tiene presupuesto o ganas de
    comprar pero NO especificó ningún tipo de producto.

    Criterio: tiene señal de presupuesto/recomendación genérica Y no contiene
    ningún sustantivo de categoría reconocible. Cuando se activa, el agente
    debe preguntar por categoría en lugar de buscar/recomendar al azar.

    Es determinístico — solo regex, sin LLM."""

    _RX_PRESUPUESTO = re.compile(
        r"\b(?:"
        r"tengo\s+(?:un\s+)?(?:presupuesto|budget|plata|lana|dinero)\b"
        r"|(?:con|manejo|mi\s+presupuesto\s+es|presupuesto\s+de)\s+\d"
        r"|tengo\s+(?:hasta\s+)?(?:bs\.?\s*)?\d"
        r"|presupuesto\s+(?:de|es|maximo|max|alto|bueno)"
        r"|buen\s+presupuesto"
        r"|no\s+hay\s+problema\s+de\s+presupuesto"
        r")\b",
        re.IGNORECASE,
    )

    _RX_RECOMENDACION_GENERICA = re.compile(
        r"\b(?:"
        r"recomiend(?:a|ame|arme|anos)\s+(?:algo|lo\s+mejor|algo\s+bueno|algo\s+util)"
        r"|que\s+(?:me\s+)?compro\b"
        r"|que\s+(?:me\s+)?(?:recomiendas|sugieres)\s*\?"
        r"|dime\s+que\s+comprar\b"
        r"|algo\s+(?:bueno|util|bonito|lindo|bacano|chevere)"
        r"|lo\s+mejor\s+(?:que\s+tengas?|disponible)"
        r"|la\s+mejor\s+opcion\s*$"
        r"|que\s+me\s+conviene\s+(?:comprar|llevar)"
        r"|que\s+(?:puedo|podria)\s+comprar"
        r"|actua\s+como\s+asesor\s+y\s+dime\s+que\s+comprar"
        r")\b",
        re.IGNORECASE,
    )

    # Palabras de categoría de producto: si alguna aparece, no es vaga
    _RX_TIENE_CATEGORIA = re.compile(
        r"\b(?:"
        r"celular|celu|smartphone|iphone|android|telefono"
        r"|laptop|compu|computadora|notebook|portatil|pc\b"
        r"|televisor|televisores|tele|tv\b|teli"
        r"|refrigeradora|refri|frigobar|freezer"
        r"|lavadora|lavadora|secadora"
        r"|tablet|ipad"
        r"|audifono|parlante|altavoz|bocina"
        r"|camara|foto|impresora"
        r"|cocina|estufa|microondas|freidora|licuadora|batidora"
        r"|consola|playstation|xbox|nintendo|gaming"
        r"|reloj|smartwatch|wearable"
        r"|monitor|proyector"
        r"|aspiradora|planchadora"
        r")\b",
        re.IGNORECASE,
    )

    @classmethod
    def es_vaga(cls, mensaje: str) -> bool:
        """True cuando hay señal de presupuesto/recomendación pero cero categoría."""
        if not mensaje:
            return False
        tiene_presupuesto = bool(cls._RX_PRESUPUESTO.search(mensaje))
        tiene_generica = bool(cls._RX_RECOMENDACION_GENERICA.search(mensaje))
        if not (tiene_presupuesto or tiene_generica):
            return False
        return not bool(cls._RX_TIENE_CATEGORIA.search(mensaje))

    RESPUESTA = (
        "¡Con gusto te ayudo a elegir! Para darte la mejor recomendación, "
        "necesito saber qué tipo de producto estás buscando. "
        "Por ejemplo: televisor, celular, laptop, refrigeradora, lavadora, "
        "tablet, audífonos… ¿Qué tenés en mente?"
    )

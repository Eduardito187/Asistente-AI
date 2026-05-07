from __future__ import annotations

import re


class DetectorDespedida:
    """Detecta cuando el cliente está cerrando la conversación.

    Casos:
    - Despedida explícita: "gracias, chao", "hasta luego", "ya, listo"
    - Cierre suave: "bueno, lo voy a pensar", "te aviso", "después decido"
    - Salida abrupta: "ya, gracias", "ok, gracias"

    No corta el flujo — alimenta el bloque de contexto al LLM. Si el cliente
    NO compró nada en la sesión, el LLM debe ofrecer (1) la red de contacto
    de ventas como fallback, (2) un cierre cordial, (3) un guardar carrito
    si dejó productos sin confirmar."""

    # Mensaje completo (anchored): el cliente cerró si TODO el mensaje es una
    # forma de despedida. Esto evita falsos positivos con frases tipo
    # "gracias por explicarme, ¿cuál es el precio?" donde "gracias" aparece
    # pero la conversación continúa.
    _RX_MENSAJE_COMPLETO = re.compile(
        r"^\s*"
        r"(?:bueno|listo|ok|okay|perfecto|de\s+acuerdo|dale|ya)?\s*[,.]?\s*"
        r"(?:"
        r"chao|chau|adi[óo]s|bye"
        r"|hasta\s+(?:luego|pronto|la\s+vista|ma[ñn]ana|otra|despu[ée]s|nunca)"
        r"|nos\s+vemos"
        r"|me\s+voy(?:\s+ya)?"
        r"|me\s+retiro"
        r"|gracias(?:\s+(?:por\s+(?:todo|nada|tu\s+ayuda|la\s+ayuda))?)?(?:\s+chao|"
        r"\s+chau|\s+adi[óo]s|\s+nada\s+m[áa]s)?"
        r"|much(?:as|[íi]simas)\s+gracias(?:\s+(?:por\s+todo|chao|chau|nada\s+m[áa]s))?"
        r"|mil\s+gracias"
        r"|listo(?:\s+gracias)?"
        r"|nada\s+m[áa]s(?:\s+gracias)?"
        r"|(?:no|nada),?\s+gracias"
        r"|ya\s+(?:est[áa]|esta|listo|fue)"
        r")"
        r"\s*[!.]*\s*$",
        re.IGNORECASE,
    )

    # Cierre suave / pospuesto: pueden aparecer en mitad de una frase larga
    # ("bueno, lo voy a pensar y te aviso después") y siguen contando como
    # despedida porque el cliente está saliendo.
    _RX_CIERRE_SUAVE = re.compile(
        r"(?:"
        r"\blo\s+voy\s+a\s+(?:pensar|pensarlo|consultar|revisar)\b"
        r"|\b(?:te|le)\s+aviso\s+(?:despu[ée]s|m[áa]s\s+tarde|luego|cuando)"
        r"|\bdespu[ée]s\s+(?:te|le)?\s*(?:decido|aviso|veo|paso|escribo)"
        r"|\bm[áa]s\s+tarde\s+(?:te|le)?\s*(?:vuelvo|regreso|aviso)"
        r"|\botro\s+d[íi]a\s+vuelvo\b"
        r"|\bser[áa]\s+(?:para|en)\s+otro\s+momento\b"
        r"|\botra\s+vez\s+(?:ser[áa]|vuelvo)\b"
        r"|\bgracias\s+por\s+(?:nada|todo)\b"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def es_despedida(cls, mensaje: str) -> bool:
        if not mensaje:
            return False
        texto = mensaje.strip()
        # Mensaje completo es despedida (caso fuerte, evita falsos positivos)
        if cls._RX_MENSAJE_COMPLETO.match(texto):
            return True
        # O contiene una expresión de cierre pospuesto (te aviso, lo pienso)
        return bool(cls._RX_CIERRE_SUAVE.search(texto))

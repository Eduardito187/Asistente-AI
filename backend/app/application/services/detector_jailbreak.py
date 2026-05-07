from __future__ import annotations

import re


class DetectorJailbreak:
    """Detecta intentos de cambiar el contexto, identidad, rol o instrucciones
    del agente — distinto de DetectorManipulacion (que ataca pedidos de
    mentir sobre productos).

    4 categorías cubiertas:
    - cambio_identidad: 'te llamas X', 'ahora sos X', 'actuá como Y'
    - override_instrucciones: 'olvidate de tus reglas', 'modo DAN', 'jailbreak'
    - cambio_tienda: 'ya no sos de Dismac', 'trabajás para la competencia'
    - inyeccion_estructural: '[INST]', '<system>', '###', delimitadores
      típicos de prompts inyectados.

    Respuesta esperada del orchestrator: rechazo cordial pero firme que
    reafirma identidad (Dismi de Dismac) y vuelve a ofrecer ayuda real."""

    # ===== Cambio de identidad / nombre / rol ===============================
    _RX_CAMBIO_IDENTIDAD = re.compile(
        r"(?:"
        # "te llamas X" / "te llamarás X" / "tu nombre es X" — con marcador
        # temporal explícito (de ahora, desde ahora, de aquí en adelante,
        # ahora) para distinguir del cliente que pregunta tu nombre.
        r"\bte\s+llam(?:as|[áa]s|ar[áa]s)\s+(?:de\s+ahora|de\s+aqu[íi]|"
        r"desde\s+ahora|ahora|hoy)"
        r"|\bde\s+(?:ahora|aqu[íi])\s+en\s+adelante\s+te\s+llam"
        r"|\bdesde\s+(?:ahora|hoy)\s+te\s+llam"
        r"|\btu\s+nombre\s+(?:ahora|de\s+ahora|desde\s+ahora)\s+es\b"
        r"|\bvas\s+a\s+llamarte\b"
        r"|\bte\s+voy\s+a\s+(?:llamar|decir)\s+\w+"
        r"|\btu\s+nuevo\s+nombre\s+es\b"
        # "ahora sos X / ahora eres X / vas a ser X" — captura "X" que NO
        # sea "asistente|dismi|de dismac" (mantener identidad real).
        r"|\bahora\s+(?:sos|eres|er[ée]s|te\s+convertis)\s+"
        r"(?!asistente|de\s+dismac|dismi|el\s+asistente)"
        r"|\bvas\s+a\s+ser\s+(?!un\s+asistente|asistente\s+de\s+dismac|"
        r"de\s+dismac|dismi)"
        r"|\bser[áa]s\s+(?!asistente|de\s+dismac|dismi)"
        r"|\bdesde\s+(?:ahora|ya)\s+(?:sos|eres)\b"
        # Pretender / actuar / hacerse pasar
        r"|\bact[úu][aá](?:r|me)?\s+como\s+(?!asistente|asesor|dismi)"
        r"|\bactuar\s+como\s+(?!asistente|asesor|dismi)"
        r"|\bpret[ée]nd[ae](?:r|te)?\s+(?:ser|que\s+sos|que\s+eres)"
        r"|\bhac[ée](?:te)?\s+pasar\s+por\b"
        r"|\bhac[ée]me\s+(?:de\s+cuenta|cuenta)\s+que\s+(?:sos|eres)"
        r"|\bjuga(?:r|te)?\s+a\s+ser\b"
        r"|\bsimul[áa]\s+ser\b"
        r"|\bfing[ií]\s+(?:ser|que\s+sos|que\s+eres)"
        r"|\brole[\s_-]*play\b"
        r"|\brolepl[aeiou]+y\b"  # tolera typos comunes (rolepleay, roleplaay)
        r")",
        re.IGNORECASE,
    )

    # ===== Override de instrucciones / jailbreak ============================
    _RX_OVERRIDE_INSTRUCCIONES = re.compile(
        r"(?:"
        # Olvidar / ignorar / descartar instrucciones
        r"\bolvid(?:a|[áa](?:te)?)\s+(?:de\s+)?(?:tus?|todas?\s+(?:tus?|las)|las)\s+"
        r"(?:instrucci|reglas?|directiv|prompts?|systems?|configur|programaci)"
        r"|\bignor[áa](?:r|me|en)?\s+(?:todo\s+)?(?:lo\s+anterior|"
        r"todas?\s+(?:tu|las)\s+instrucci|el\s+(?:system|prompt)|"
        r"las\s+reglas|tus\s+(?:reglas|directrices|instrucci))"
        r"|\bdescart[áa](?:r|me)?\s+(?:lo\s+anterior|tus\s+(?:instrucci|reglas))"
        r"|\breseteate\b|\breset[ée]\s+(?:tu|las|el\s+sistema)"
        r"|\bborra\s+(?:tu|todas?\s+las?)\s+(?:memoria|instrucci|reglas)"
        r"|\bdeja\s+de\s+(?:ser|seguir|comportarte\s+como)\s+"
        r"(?:asistente|dismi|de\s+dismac)"
        r"|\bsobre\s*escrib[íi](?:r|me)?\s+(?:tu|el)\s+(?:prompt|system|instrucci)"
        # Modos jailbreak conocidos
        r"|\bmodo\s+(?:dios|libre|sin\s+restricci|sin\s+filtros?|"
        r"desarrollador|developer|admin|root|debug|hack)"
        r"|\bjail\s*break\b"
        r"|\bdan\s+(?:mode|modo|version|prompt)\b|\bmodo\s+dan\b"
        r"|\bdo\s+anything\s+now\b"
        r"|\bsin\s+(?:filtros?|censura|restricci|reglas|limit)"
        r"|\bsin\s+ning[úu]n\s+(?:filtro|l[íi]mite|restricci)"
        # "Eres libre de hacer..."
        r"|\beres\s+libre\s+de\s+hacer\b"
        r"|\bsos\s+libre\s+de\s+hacer\b"
        r")",
        re.IGNORECASE,
    )

    # ===== Cambio de tienda / marca empleadora ===============================
    _RX_CAMBIO_TIENDA = re.compile(
        r"(?:"
        r"\bya\s+no\s+(?:sos|eres|trabajas?|representas|atendes)\s+"
        r"(?:de\s+|para\s+|en\s+)?dismac"
        r"|\bya\s+no\s+representas\s+a\s+dismac"
        r"|\btrabaj[áa]s\s+(?:para|en|con)\s+(?:hipermaxi|ice|fassil|"
        r"sas|s[áa]ez|fierro|otra\s+tienda|la\s+competencia)"
        r"|\bahora\s+trabaj[áa]s\s+(?:para|en|con)\s+(?!dismac)"
        r"|\bsos\s+(?:vendedor|asistente|empleado|representante|trabajador)\s+"
        r"(?:de\s+)?(?:la\s+)?(?:hipermaxi|ice|fassil|otra\s+tienda|"
        r"competencia|otro\s+negocio|otra\s+marca)"
        r"|\bcambi[áa]\s+de\s+(?:empresa|tienda|marca)\b"
        r"|\bahora\s+vend[ée]s\s+(?:para|en)\s+(?!dismac)"
        r"|\bya\s+no\s+sos\s+dismi\b"
        r")",
        re.IGNORECASE,
    )

    # ===== Inyección estructural (delimitadores de prompt) ===================
    _RX_INYECCION_ESTRUCTURAL = re.compile(
        r"(?:"
        r"\[/?INST\]"
        r"|<\s*/?\s*system\s*>"
        r"|<\s*/?\s*\|?\s*(?:system|user|assistant|im_start|im_end)\s*\|?\s*>"
        r"|###\s*(?:system|instruction|new\s+instruction|nueva\s+instrucci)"
        r"|\bbegin\s+(?:new\s+)?(?:instruction|system|prompt)"
        r"|\bend\s+of\s+(?:system|prompt|instruction)"
        r"|\bnueva\s+instrucci[óo]n\s+del\s+sistema"
        r"|\bsystem\s*:\s*ahora\b"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def es_jailbreak(cls, mensaje: str) -> bool:
        return cls.tipo(mensaje) is not None

    @classmethod
    def tipo(cls, mensaje: str) -> str | None:
        """Devuelve el tipo de intento detectado o None si el mensaje es
        legítimo. Útil para métricas (`ruta=rechazo_jailbreak_<tipo>`)."""
        if not mensaje:
            return None
        if cls._RX_INYECCION_ESTRUCTURAL.search(mensaje):
            return "inyeccion_estructural"
        if cls._RX_OVERRIDE_INSTRUCCIONES.search(mensaje):
            return "override_instrucciones"
        if cls._RX_CAMBIO_IDENTIDAD.search(mensaje):
            return "cambio_identidad"
        if cls._RX_CAMBIO_TIENDA.search(mensaje):
            return "cambio_tienda"
        return None

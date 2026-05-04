from __future__ import annotations

from enum import Enum


class TonoDismi(str, Enum):
    """Tonos disponibles del asesor. Adapta segun perfil/etapa/situacion."""
    AMIGABLE_CASUAL = "amigable_casual"      # default, voseo, ligero
    PROFESIONAL_CONCISO = "profesional_conciso"  # tecnico, sin emojis
    EMPATICO_PACIENTE = "empatico_paciente"  # cliente confundido, mucho contexto
    DIRECTO_DECIDIDO = "directo_decidido"    # cliente listo para comprar
    ASESOR_PREMIUM = "asesor_premium"        # cliente flagship, cuida formas


class MotorPersonalidadDismi:
    """SRP: elegir tono y darle al system_prompt una linea-guia segun
    perfil del comprador, etapa y senales del mensaje.

    Sin esto, el asesor habla igual a un universitario y a un CEO. Aqui
    le inyectamos personalidad."""

    _SENIALES_LISTO_COMPRAR: tuple[str, ...] = (
        "lo llevo", "lo quiero", "comprame", "agregalo", "lo compro",
        "decidido", "listo", "ya esta", "vendi", "dame ese",
    )
    _SENIALES_CONFUNDIDO: tuple[str, ...] = (
        "no se", "estoy perdido", "no entiendo", "ayudame", "auxilio",
        "que hago", "no tengo idea", "primera vez",
    )

    @classmethod
    def elegir_tono(cls, mensaje: str, perfil_comprador: str, perfil_sesion) -> TonoDismi:
        msg = (mensaje or "").lower()
        if any(s in msg for s in cls._SENIALES_LISTO_COMPRAR):
            return TonoDismi.DIRECTO_DECIDIDO
        if any(s in msg for s in cls._SENIALES_CONFUNDIDO):
            return TonoDismi.EMPATICO_PACIENTE
        tier = (getattr(perfil_sesion, "desired_tier", None) or "").lower()
        techo = getattr(perfil_sesion, "presupuesto_max", None) or 0
        if tier in ("flagship", "premium") or techo >= 12000:
            return TonoDismi.ASESOR_PREMIUM
        if perfil_comprador in ("profesional", "empresa"):
            return TonoDismi.PROFESIONAL_CONCISO
        return TonoDismi.AMIGABLE_CASUAL

    _GUIAS: dict[TonoDismi, str] = {
        TonoDismi.AMIGABLE_CASUAL: (
            "Tono amigable, voseo es-BO, ligero. Hasta 1 emoji por respuesta. "
            "Sin formalidades excesivas pero respetuoso."
        ),
        TonoDismi.PROFESIONAL_CONCISO: (
            "Tono profesional, sin emojis. Datos primero, narrativa despues. "
            "Frases cortas. Sin diminutivos ni jerga."
        ),
        TonoDismi.EMPATICO_PACIENTE: (
            "Tono empatico. Reconoce que es mucha info. Usa frases tipo 'tranquilo', "
            "'vamos paso a paso'. Explica con analogias cotidianas."
        ),
        TonoDismi.DIRECTO_DECIDIDO: (
            "Tono directo. El cliente decidio. Confirma el modelo, precio, stock y "
            "siguiente paso (pago/envio). NO ofrezcas mas alternativas."
        ),
        TonoDismi.ASESOR_PREMIUM: (
            "Tono asesor premium. Mas pulido, sin abreviaturas. Destaca calidad de "
            "marca, garantia, soporte post-venta. El precio NO es el filtro principal."
        ),
    }

    @classmethod
    def guia_para_prompt(cls, tono: TonoDismi) -> str:
        return cls._GUIAS.get(tono, cls._GUIAS[TonoDismi.AMIGABLE_CASUAL])

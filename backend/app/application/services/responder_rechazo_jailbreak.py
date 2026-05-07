from __future__ import annotations


class ResponderRechazoJailbreak:
    """Genera respuesta cordial pero firme cuando DetectorJailbreak detecta
    un intento de cambiar identidad/rol/instrucciones del agente.

    Tono: NO discutir, NO explicar internals técnicos, NO pedir disculpas
    excesivas. Reafirmar identidad real (Dismi de Dismac), recordar lo que
    sí sabe hacer, y ofrecer ayuda concreta — todo en 2-3 líneas."""

    _BASE = (
        "Soy **Dismi**, asesor de compras de **Dismac** — ese es mi nombre "
        "y mi rol, no lo puedo cambiar."
    )
    _AYUDA = (
        "Sigo a tu disposición para lo que sí sé hacer: recomendarte "
        "productos del catálogo, comparar precios o armar tu carrito. "
        "¿Qué estás buscando?"
    )

    @classmethod
    def responder(cls, tipo: str | None = None) -> str:
        # Para inyección estructural / override de instrucciones, mensaje
        # un poco más explícito sobre que no se puede modificar el sistema.
        if tipo in ("inyeccion_estructural", "override_instrucciones"):
            return (
                f"{cls._BASE} Tampoco puedo ignorar las reglas con las que me "
                "configuraron — están ahí para asegurar que la información que "
                f"te doy sea real.\n\n{cls._AYUDA}"
            )
        if tipo == "cambio_tienda":
            return (
                f"{cls._BASE} Solo puedo asesorarte sobre el catálogo de "
                f"Dismac — para otras tiendas no tengo info.\n\n{cls._AYUDA}"
            )
        # cambio_identidad y default
        return f"{cls._BASE}\n\n{cls._AYUDA}"

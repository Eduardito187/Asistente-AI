from __future__ import annotations

import re


class DetectorIntencionCompraInmediata:
    """Detecta señales de compra inmediata: el cliente ya decidió y quiere
    cerrar la transacción ahora. Expresiones bolivianas y latinas incluidas.
    Cuando dispara, el agente debe priorizar agregar al carrito / confirmar
    en lugar de seguir mostrando más opciones."""

    _RX = re.compile(
        r"(?:"
        # Expresiones directas de llevar/comprar
        r"\blo\s+llevo\b"
        r"|\bla\s+llevo\b"
        r"|\blos\s+llevo\b"
        r"|\blas\s+llevo\b"
        r"|\bme\s+lo\s+llevo\b"
        r"|\bme\s+la\s+llevo\b"
        r"|\bme\s+quedo\s+con\s+(?:ese|esa|eso|este|esta|esto|el|la)\b"
        # Bolivian "de frente / de una / al tiro"
        r"|\bde\s+frente\b"                      # de frente = ahora mismo
        r"|\bde\s+una\b"                          # de una = inmediatamente
        r"|\bal\s+tiro\b"                         # al tiro = ahora (Chile/BO)
        r"|\bde\s+una\s+vez\b"
        r"|\bahorita\s+(?:mismo\s+)?(?:lo\s+quiero|me\s+lo\s+llevo|lo\s+compro)\b"
        # Compra explícita
        r"|\blo\s+compro\b"
        r"|\bla\s+compro\b"
        r"|\bquiero\s+(?:comprarlo|comprarlo|comprarla|comprar\s+(?:ese|esa|este|esta))\b"
        r"|\bme\s+(?:lo|la)\s+(?:vendo|vendes?|puede\s+vender)\b"
        # Agregar al carrito explícito
        r"|\bagr[eé]ga(?:lo|la|me)\b"
        r"|\bponelo\s+(?:en\s+el\s+)?(?:carrito|carro)\b"
        r"|\b(?:al|en\s+el)\s+carrito\b"
        r"|\bañad[eíi](?:lo|la|me)\b"
        # Jale/saque boliviano con intención clara
        r"|\bjalo\s+(?:ese|esa|el|la|este|esta)\b"
        r"|\bme\s+jalo\s+(?:ese|esa|el|la|este|esta)\b"
        # Confirmar compra
        r"|\bconfirm[ao]\b"
        r"|\bconfirmar\s+(?:la\s+)?(?:compra|orden|pedido)\b"
        r"|\bprocede\b"
        r"|\bproceder\b"
        r"|\bvamos\s+con\s+(?:ese|esa|ese|ese)\b"
        r"|\beso\s+(?:quiero|me\s+llevo)\b"
        r"|\bese\s+(?:mismo|mero)\b"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def es_compra_inmediata(cls, mensaje: str) -> bool:
        """True cuando el cliente señala intención de compra inmediata."""
        if not mensaje:
            return False
        return bool(cls._RX.search(mensaje))

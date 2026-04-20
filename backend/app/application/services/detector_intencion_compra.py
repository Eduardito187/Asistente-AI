from __future__ import annotations

import re


class DetectorIntencionCompra:
    """SRP: detectar que el cliente ya decidio comprar / reservar.

    Gatilla cuando el cliente pide cerrar la venta sobre un producto mostrado:
      - 'quiero comprar esa / ese'
      - 'me interesa ese, como pago'
      - 'reservamelo'
      - 'me lo llevo'
      - 'procedamos con la compra'

    Uso: cuando dispara, el agente debe guiar al flujo de confirmacion
    (agregar_al_carrito + confirmar_orden con datos del cliente) en vez de
    seguir recomendando o listar alternativas. Detector puramente regex."""

    _RX_INTENCION = re.compile(
        r"\b(?:"
        r"quiero\s+(?:comprar|llevarlo|llevarla|llevarme|reservar)"
        r"|me\s+(?:interesa|gusta|convence|convencio)\s+(?:ese|esa|este|esta)\b"
        r"|me\s+lo\s+(?:llevo|quedo|compro)"
        r"|me\s+la\s+(?:llevo|quedo|compro)"
        r"|lo\s+(?:compro|llevo|quiero)\s*(?:ya|ahora)?"
        r"|la\s+(?:compro|llevo|quiero)\s*(?:ya|ahora)?"
        r"|(?:reserva|reservame|reserva\s+me|apartame|guardame)(?:lo|la|la\s+)?"
        r"|procedamos\s+con\s+la\s+compra"
        r"|finaliza(?:me|r)?\s+(?:la\s+)?compra"
        r"|cerremos\s+(?:la\s+)?compra"
        r"|(?:como|donde)\s+(?:pago|pagar|te\s+pago)"
        r"|cual\s+es\s+el\s+siguiente\s+paso"
        r"|dale\s+confirma(?:r|me)?"
        r")\b",
        re.IGNORECASE,
    )

    @classmethod
    def tiene_intencion(cls, texto: str) -> bool:
        if not texto:
            return False
        return bool(cls._RX_INTENCION.search(texto))

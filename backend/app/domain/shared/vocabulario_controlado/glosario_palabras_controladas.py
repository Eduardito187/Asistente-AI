from __future__ import annotations

from .reemplazo_palabra import ReemplazoPalabra


class GlosarioPalabrasControladas:
    """Fuente de verdad única de palabras prohibidas y sus sustitutos.

    Para agregar una nueva palabra prohibida: añadir un ReemplazoPalabra a
    _REGLAS. El FiltroVocabularioControlado se recompila automáticamente.
    """

    _REGLAS: tuple[ReemplazoPalabra, ...] = (
        ReemplazoPalabra(mapa=(
            ("descuento",      "ahorro"),
            ("descuentos",     "ahorros"),
            ("descuentazo",    "gran ahorro"),
            ("descuentazos",   "grandes ahorros"),
            ("descuentito",    "pequeño ahorro"),
            ("descuentitos",   "pequeños ahorros"),
        )),
    )

    @classmethod
    def reglas(cls) -> tuple[ReemplazoPalabra, ...]:
        return cls._REGLAS

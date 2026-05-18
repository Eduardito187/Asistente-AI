from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReemplazoPalabra:
    """VO inmutable: mapea cada forma prohibida a su sustituto aprobado.

    Usar tuplas de pares en lugar de dict para mantener hashability.
    Ejemplo:
        ReemplazoPalabra(mapa=(
            ("descuento", "ahorro"),
            ("descuentos", "ahorros"),
        ))
    """

    mapa: tuple[tuple[str, str], ...]

    def formas_prohibidas(self) -> tuple[str, ...]:
        return tuple(par[0] for par in self.mapa)

    def sustituto(self, forma: str) -> str | None:
        clave = forma.lower()
        for prohibida, aprobada in self.mapa:
            if prohibida.lower() == clave:
                return aprobada
        return None

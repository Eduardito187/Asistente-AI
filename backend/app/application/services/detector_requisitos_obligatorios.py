from __future__ import annotations

import re

from .parser_presupuesto import ParserPresupuesto


class DetectorRequisitosObligatorios:
    """SRP: detecta la sintaxis 'Obligatorio: X' / 'Preferible: X' en mensajes
    donde el cliente diferencia explícitamente filtros duros de sugerencias.

    El caller usa esta clase para suprimir filtros blandos del pipeline SQL y
    dejar que el LLM los aplique solo como criterio de ranking, no como WHERE.
    """

    _RX_PREF = re.compile(r"preferible[s]?\s*:\s*([^\n.;]+)", re.IGNORECASE)
    _RX_OBLIG = re.compile(r"obligatorio[s]?\s*:\s*([^\n.;]+)", re.IGNORECASE)

    @classmethod
    def precio_es_preferible(cls, mensaje: str | None) -> bool:
        """True si el presupuesto aparece solo en la sección 'Preferible:'.

        Ejemplo: 'Obligatorio: GPU dedicada. Preferible: que no pase de 8000 Bs.'
        → el precio 8000 NO debe convertirse en un filtro precio_max duro."""
        for m in cls._RX_PREF.finditer(mensaje or ""):
            if ParserPresupuesto.extraer(m.group(1)) is not None:
                return True
        return False

    @classmethod
    def bloque_obligatorio(cls, mensaje: str | None) -> str:
        """Texto de todos los bloques 'Obligatorio: ...' concatenados."""
        partes = [m.group(1).strip() for m in cls._RX_OBLIG.finditer(mensaje or "")]
        return " ".join(partes)

    @classmethod
    def bloque_preferible(cls, mensaje: str | None) -> str:
        """Texto de todos los bloques 'Preferible: ...' concatenados."""
        partes = [m.group(1).strip() for m in cls._RX_PREF.finditer(mensaje or "")]
        return " ".join(partes)

    @classmethod
    def hay_sintaxis(cls, mensaje: str | None) -> bool:
        """True si el mensaje usa la sintaxis Obligatorio/Preferible."""
        texto = mensaje or ""
        return bool(cls._RX_OBLIG.search(texto) or cls._RX_PREF.search(texto))

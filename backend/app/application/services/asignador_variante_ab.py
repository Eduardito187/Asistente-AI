from __future__ import annotations

import hashlib
from uuid import UUID


class AsignadorVarianteAB:
    """Asigna deterministamente una variante A/B/C... a una sesión.

    Determinismo: la misma sesion_id siempre cae en la misma variante (no
    cambia entre turnos). Distribución uniforme via sha256 + módulo.

    Uso típico: testear variantes del mensaje de derivación a ventas para
    medir cuál funciona mejor. La variante asignada se persiste en la
    métrica del turno (`variante_ab`) para análisis posterior."""

    @classmethod
    def variante(cls, sesion_id: UUID, opciones: tuple[str, ...]) -> str:
        """Devuelve una de las opciones según el hash de sesion_id."""
        if not opciones:
            return ""
        h = hashlib.sha256(str(sesion_id).encode()).hexdigest()
        idx = int(h[:8], 16) % len(opciones)
        return opciones[idx]

    @classmethod
    def es_variante_a(cls, sesion_id: UUID, opciones: tuple[str, ...]) -> bool:
        """Helper: True si la sesión cae en la primera opción."""
        return cls.variante(sesion_id, opciones) == opciones[0]

from __future__ import annotations

import re
from typing import Optional

from ...domain.shared.normalizacion import NormalizadorTexto


class DetectorTierDeseado:
    """SRP: detecta el TIER (gama) al que apunta el cliente con frases como
    'tope de gama', 'premium', 'flagship', 'económico', 'barato'.
    Devuelve un valor normalizado del enum {flagship, alto, medio, budget}
    o None si el mensaje no indica tier.

    El tier se persiste en `perfiles_sesion.desired_tier` y condiciona el
    filtrado/ranking del catálogo (ej. si tier=flagship, low-end se excluye)."""

    # Orden importa: primero flagship (más específico) para que "tope de gama
    # premium" no matchee como "medio".
    _RX_FLAGSHIP = re.compile(
        r"\b(?:tope\s+de\s+gama|tope\s+gama|alta\s+gama|gama\s+alta|premium|"
        r"flagship|high[\s-]?end|lo\s+mejor|el\s+mejor|la\s+mejor|"
        r"maxima\s+gama|gama\s+maxima)\b",
        re.IGNORECASE,
    )
    _RX_ALTO = re.compile(
        r"\b(?:gama\s+alta[-\s]?media|media[-\s]?alta|mejor\s+de\s+lo\s+medio|"
        r"bueno\s+pero\s+no\s+tope)\b",
        re.IGNORECASE,
    )
    _RX_MEDIO = re.compile(
        r"\b(?:gama\s+media|equilibrado|precio[\s-]?calidad|"
        r"medio|intermedio|balanceado|value\s+for\s+money)\b",
        re.IGNORECASE,
    )
    _RX_BUDGET = re.compile(
        r"\b(?:economico|barato|mas\s+barato|accesible|entrada|"
        r"low[\s-]?end|gama\s+baja|mas\s+accesible|low\s+cost|"
        r"lo\s+mas\s+barato|ahorrar)\b",
        re.IGNORECASE,
    )

    @classmethod
    def detectar(cls, texto: str | None) -> Optional[str]:
        if not texto:
            return None
        t = NormalizadorTexto.normalizar(texto)
        if cls._RX_FLAGSHIP.search(t):
            return "flagship"
        if cls._RX_ALTO.search(t):
            return "alto"
        if cls._RX_BUDGET.search(t):
            return "budget"
        if cls._RX_MEDIO.search(t):
            return "medio"
        return None

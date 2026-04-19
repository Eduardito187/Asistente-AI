from __future__ import annotations

import re

RX_DOLARES = re.compile(r"\$\s*(\d[\d\.,]*)")


class NormalizadorMoneda:
    """SRP: convertir cualquier cita de moneda en dolares ($) a bolivianos (Bs).

    El catalogo esta en BOB. Si el modelo se le escapa un `$5,999`, lo reescribimos
    a `Bs 5999` antes de devolver al cliente.
    """

    @classmethod
    def normalizar(cls, texto: str) -> str:
        if not texto or "$" not in texto:
            return texto
        return RX_DOLARES.sub(lambda m: f"Bs {cls._limpiar_numero(m.group(1))}", texto)

    @staticmethod
    def _limpiar_numero(valor: str) -> str:
        crudo = valor.rstrip(".,").replace(",", "")
        if "." in crudo:
            entero, _, decimales = crudo.partition(".")
            if len(decimales) <= 2:
                return entero
        return crudo

from __future__ import annotations

import hashlib
import re


class HasherContacto:
    """SRP: hash determinista (sha256) de email/telefono normalizado.
    Asi nunca persistimos el dato crudo (privacidad) pero podemos identificar
    al cliente recurrente."""

    _RX_NO_DIGITO = re.compile(r"\D+")

    @classmethod
    def email(cls, raw: str) -> str:
        norm = (raw or "").strip().lower()
        return hashlib.sha256(f"email:{norm}".encode()).hexdigest()

    @classmethod
    def telefono(cls, raw: str) -> str:
        digitos = cls._RX_NO_DIGITO.sub("", raw or "")
        if digitos.startswith("591") and len(digitos) >= 11:
            digitos = digitos[3:]
        return hashlib.sha256(f"phone:{digitos}".encode()).hexdigest()

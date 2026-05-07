from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ContactoDetectado:
    email: str | None
    telefono: str | None


class DetectorContactoCliente:
    """SRP: extraer email y telefono del mensaje del cliente para hidratar
    PerfilHistorico. NO valida formalmente — solo deteccion best-effort."""

    _RX_EMAIL = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )
    _RX_TELEFONO = re.compile(
        r"\b(?:\+?591[\s-]?)?[67]\d{7}\b"
    )

    @classmethod
    def detectar(cls, mensaje: str) -> ContactoDetectado:
        if not mensaje:
            return ContactoDetectado(email=None, telefono=None)
        m_email = cls._RX_EMAIL.search(mensaje)
        m_tel = cls._RX_TELEFONO.search(mensaje)
        return ContactoDetectado(
            email=m_email.group(0).lower() if m_email else None,
            telefono=m_tel.group(0).strip() if m_tel else None,
        )

from __future__ import annotations

import hashlib
from uuid import UUID


class GeneradorLinkSesion:
    """Genera un código corto de 8 caracteres para que el cliente retome
    la conversación. El código es determinístico por sesion_id: siempre
    el mismo para la misma sesión.

    Uso: cuando el cliente dice 'lo pienso y vuelvo', dar este código
    para que pueda retomar sin perder el contexto."""

    _PREFIX = "DIS-"

    @classmethod
    def codigo(cls, sesion_id: UUID) -> str:
        """Retorna código legible de 8 chars: DIS-XXXX."""
        h = hashlib.sha256(str(sesion_id).encode()).hexdigest()[:6].upper()
        return f"{cls._PREFIX}{h}"

    @classmethod
    def mensaje_retoma(cls, sesion_id: UUID) -> str:
        """Texto listo para incluir en respuesta cuando cliente quiere pausar."""
        codigo = cls.codigo(sesion_id)
        return (
            f"¡Perfecto! Te guardo el código de tu consulta: **{codigo}**\n"
            "Cuando vuelvas, solo mencioná este código y retomamos "
            "desde donde lo dejaste sin tener que repetir todo de nuevo."
        )

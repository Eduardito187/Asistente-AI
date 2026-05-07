from __future__ import annotations

from .detector_frustracion import DetectorFrustracion


class EvaluadorFrustracionAcumulada:
    """Detecta deterioro progresivo de la conversación usando el historial.

    Caso de uso: ningún mensaje individual es claramente frustrante (no pasa
    el filtro de DetectorFrustracion.debe_derivar), pero acumulados muestran
    al cliente perdiendo paciencia turno tras turno. Si en los últimos
    `_VENTANA` mensajes del cliente hay `_UMBRAL` con cualquier nivel
    (bajo / medio / alto), derivamos preventivamente antes de que estalle.

    No requiere cambios de schema — lee del HistorialChatHandler ya existente.
    """

    _VENTANA = 5
    _UMBRAL = 3

    @classmethod
    def debe_derivar(cls, mensajes_user_historicos: list[str], mensaje_actual: str) -> bool:
        """True si el cliente acumula `_UMBRAL` señales no-nulas en los
        últimos `_VENTANA` mensajes (incluyendo el actual)."""
        ventana = cls._ultimos(mensajes_user_historicos, cls._VENTANA - 1)
        ventana.append(mensaje_actual or "")
        return cls._cuenta_senales(ventana) >= cls._UMBRAL

    @classmethod
    def cuenta_senales_recientes(cls, mensajes_user_historicos: list[str], mensaje_actual: str) -> int:
        """Cuenta señales para métricas / debug."""
        ventana = cls._ultimos(mensajes_user_historicos, cls._VENTANA - 1)
        ventana.append(mensaje_actual or "")
        return cls._cuenta_senales(ventana)

    @staticmethod
    def _ultimos(items: list[str], n: int) -> list[str]:
        if not items:
            return []
        return list(items[-n:])

    @staticmethod
    def _cuenta_senales(ventana: list[str]) -> int:
        return sum(
            1 for m in ventana
            if m and DetectorFrustracion.nivel(m) in ("alto", "medio", "bajo")
        )

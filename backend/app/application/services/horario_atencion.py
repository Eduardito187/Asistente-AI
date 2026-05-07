from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from typing import Optional


class HorarioAtencion:
    """Determina si el equipo humano de ventas Dismac está atendiendo ahora.

    Usado para adaptar mensajes de derivación: si está abierto, el cliente
    puede llamar/wsp ya; si está cerrado, le decimos que escriba ahora pero
    le respondemos al día siguiente.

    Bolivia: timezone fija UTC-4 (no tiene DST). Si el deploy se mueve a
    otro país, ajustar `_TZ_OFFSET_HORAS`."""

    # Lunes=0 ... Domingo=6
    _DIAS_LABORALES = frozenset({0, 1, 2, 3, 4})  # L-V
    _DIAS_SABADO = frozenset({5})
    _HORA_APERTURA = time(8, 0)
    _HORA_CIERRE = time(18, 0)
    _HORA_CIERRE_SABADO = time(13, 0)
    _TZ_OFFSET_HORAS = -4  # America/La_Paz (UTC-4 fijo, sin DST)

    @classmethod
    def dentro_horario(cls, ahora: Optional[datetime] = None) -> bool:
        """True si en este momento el equipo humano de ventas atiende."""
        local = cls._a_hora_local(ahora or datetime.now(timezone.utc))
        dia = local.weekday()
        hora_local = local.time()
        if dia in cls._DIAS_LABORALES:
            return cls._HORA_APERTURA <= hora_local < cls._HORA_CIERRE
        if dia in cls._DIAS_SABADO:
            return cls._HORA_APERTURA <= hora_local < cls._HORA_CIERRE_SABADO
        return False  # Domingo: cerrado

    @classmethod
    def descripcion_horario(cls) -> str:
        """Texto humano para incluir en respuestas off-hours."""
        return "Lunes a viernes 8:00–18:00, sábados 8:00–13:00 (hora de Bolivia)"

    @classmethod
    def proxima_apertura(cls, ahora: Optional[datetime] = None) -> str:
        """Texto sugiriendo el próximo turno laboral. Best-effort, no exacto."""
        local = cls._a_hora_local(ahora or datetime.now(timezone.utc))
        dia = local.weekday()
        hora_local = local.time()
        # Si estamos antes de apertura del mismo día y hoy es laboral, abre hoy
        if dia in cls._DIAS_LABORALES and hora_local < cls._HORA_APERTURA:
            return "hoy a las 8:00 AM"
        if dia in cls._DIAS_SABADO and hora_local < cls._HORA_APERTURA:
            return "hoy sábado a las 8:00 AM"
        # Si es viernes después de cierre o sábado tarde, abre lunes
        if dia == 4 and hora_local >= cls._HORA_CIERRE:
            return "el lunes a las 8:00 AM"
        if dia == 5:
            return "el lunes a las 8:00 AM"
        if dia == 6:  # domingo
            return "el lunes a las 8:00 AM"
        # Si es L-J después de cierre, mañana
        return "mañana a las 8:00 AM"

    @classmethod
    def _a_hora_local(cls, dt: datetime) -> datetime:
        """Convierte a hora local Bolivia (UTC-4 fijo)."""
        if dt.tzinfo is None:
            # Sin timezone: asumimos UTC.
            dt = dt.replace(tzinfo=timezone.utc)
        offset = timezone(timedelta(hours=cls._TZ_OFFSET_HORAS))
        return dt.astimezone(offset)

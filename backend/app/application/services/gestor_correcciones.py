from __future__ import annotations

import logging
from uuid import UUID

from ..commands.actualizar_perfil_sesion import (
    ActualizarPerfilSesionCommand,
    ActualizarPerfilSesionHandler,
)
from ..queries.obtener_perfil_sesion import (
    ObtenerPerfilSesionHandler,
    ObtenerPerfilSesionQuery,
)
from .detector_correccion_atributo import DetectorCorreccionAtributo

log = logging.getLogger("gestor_correcciones")

# Campos numéricos mínimos del perfil que pueden ser corregidos.
_CAMPOS_NUMERICOS = frozenset([
    "ram_gb_min", "capacidad_gb_min", "refresh_hz_min",
    "bateria_mah_min", "camara_mp_min", "capacidad_kg_min", "potencia_w_min",
])
_CAMPOS_BOOL = frozenset([
    "nfc", "usb_c", "bluetooth_incluido", "hdmi_2_1",
    "soporta_5g", "inverter", "no_frost", "smart_tv",
])


class GestorCorrecciones:
    """SRP: detecta correcciones de atributos en el mensaje del cliente y las
    persiste en el perfil antes de que el pipeline normal corra.

    Corre en el pipeline principal antes del short-circuit de declaración,
    para que la búsqueda forzada ya vea el valor corregido."""

    def __init__(
        self,
        obtener_perfil: ObtenerPerfilSesionHandler,
        actualizar_perfil: ActualizarPerfilSesionHandler,
    ) -> None:
        self._obtener_perfil = obtener_perfil
        self._actualizar_perfil = actualizar_perfil

    def aplicar_si_hay(self, mensaje: str, sesion_id: UUID) -> bool:
        """Detecta correcciones y las persiste. Devuelve True si se aplicó al menos una."""
        perfil = self._obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sesion_id))
        perfil_campos = {
            "ram_gb_min": perfil.ram_gb_min,
            "capacidad_gb_min": perfil.ssd_gb_min,
            "refresh_hz_min": perfil.refresh_hz_min,
            "bateria_mah_min": perfil.bateria_mah_min,
        }
        correcciones = DetectorCorreccionAtributo.detectar(mensaje, perfil_campos)
        if not correcciones:
            return False
        # capacidad_gb_min es el nombre interno del detector; el Command lo llama ssd_gb_min
        _ALIAS = {"capacidad_gb_min": "ssd_gb_min"}
        kwargs: dict = {"sesion_id": sesion_id}
        for c in correcciones:
            if c.campo in _CAMPOS_NUMERICOS or c.campo in _CAMPOS_BOOL or c.campo == "sistema_operativo":
                campo_cmd = _ALIAS.get(c.campo, c.campo)
                kwargs[campo_cmd] = c.valor
                log.debug("correccion detectada: %s=%s (confianza=%s)", c.campo, c.valor, c.confianza)
        if len(kwargs) <= 1:
            return False
        try:
            self._actualizar_perfil.ejecutar(ActualizarPerfilSesionCommand(**kwargs))
        except Exception as exc:
            log.warning("no se pudo aplicar correccion de atributo: %s", exc)
            return False
        return True

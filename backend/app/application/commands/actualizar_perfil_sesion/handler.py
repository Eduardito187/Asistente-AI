from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from ....domain.perfiles_sesion import PerfilSesion
from ...ports import UnitOfWork
from .command import ActualizarPerfilSesionCommand

log = logging.getLogger("actualizar_perfil_sesion")


class ActualizarPerfilSesionHandler:
    """Handler CQRS: persiste (upsert) el perfil de la sesion. No debe tirar el chat."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: ActualizarPerfilSesionCommand) -> None:
        if not cmd.tiene_datos():
            return
        perfil = PerfilSesion(
            sesion_id=cmd.sesion_id,
            presupuesto_max=cmd.presupuesto_max,
            marca_preferida=cmd.marca_preferida,
            categoria_foco=cmd.categoria_foco,
            uso_declarado=cmd.uso_declarado,
            pulgadas=cmd.pulgadas,
            tipo_panel=cmd.tipo_panel,
            resolucion=cmd.resolucion,
            updated_at=datetime.now(timezone.utc),
            subcategoria_foco=cmd.subcategoria_foco,
            genero_declarado=cmd.genero_declarado,
            sku_foco=cmd.sku_foco,
            desired_tier=cmd.desired_tier,
            ram_gb_min=cmd.ram_gb_min,
            gpu_dedicada=cmd.gpu_dedicada,
            ssd_gb_min=cmd.ssd_gb_min,
            capacidad_litros_min=cmd.capacidad_litros_min,
            nombre_excluye_acum=cmd.nombre_excluye_nuevas,
            presupuesto_ideal=cmd.presupuesto_ideal,
            presupuesto_min_buscado=cmd.presupuesto_min_buscado,
            frustracion_count=cmd.frustracion_delta,
            ciudad_sesion=cmd.ciudad_sesion,
            notas_usuario=cmd.nota_nueva,
            refresh_hz_min=cmd.refresh_hz_min,
            bateria_mah_min=cmd.bateria_mah_min,
            camara_mp_min=cmd.camara_mp_min,
            soporta_5g=cmd.soporta_5g,
            sistema_operativo=cmd.sistema_operativo,
            capacidad_kg_min=cmd.capacidad_kg_min,
            potencia_w_min=cmd.potencia_w_min,
            inverter=cmd.inverter,
            no_frost=cmd.no_frost,
            smart_tv=cmd.smart_tv,
            bluetooth_incluido=cmd.bluetooth_incluido,
            nfc=cmd.nfc,
            usb_c=cmd.usb_c,
            hdmi_2_1=cmd.hdmi_2_1,
        )
        try:
            with self._uow_factory() as uow:
                uow.perfiles_sesion.guardar(perfil)
                uow.commit()
        except Exception as exc:
            log.warning("no se pudo guardar perfil de sesion: %s", exc)

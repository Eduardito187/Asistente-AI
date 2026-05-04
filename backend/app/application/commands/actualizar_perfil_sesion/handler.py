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
            nombre_excluye_acum=cmd.nombre_excluye_nuevas,
            presupuesto_ideal=cmd.presupuesto_ideal,
        )
        try:
            with self._uow_factory() as uow:
                uow.perfiles_sesion.guardar(perfil)
                uow.commit()
        except Exception as exc:
            log.warning("no se pudo guardar perfil de sesion: %s", exc)

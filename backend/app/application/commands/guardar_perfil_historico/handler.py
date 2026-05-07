from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from ....domain.perfiles_historicos import PerfilHistorico
from ...ports import UnitOfWork
from .command import GuardarPerfilHistoricoCommand

log = logging.getLogger("guardar_perfil_historico")


class GuardarPerfilHistoricoHandler:
    """Handler CQRS: upsert sobre perfiles_historicos. Falla silenciosa."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: GuardarPerfilHistoricoCommand) -> None:
        ahora = datetime.now(timezone.utc)
        perfil = PerfilHistorico(
            id=None,
            contacto_hash=cmd.contacto_hash,
            perfil_snapshot=cmd.perfil_snapshot,
            ultima_categoria=cmd.ultima_categoria,
            ultima_marca=cmd.ultima_marca,
            ultima_compra_sku=cmd.ultima_compra_sku,
            visitas=1,
            primera_vez=ahora,
            ultima_vez=ahora,
        )
        try:
            with self._uow_factory() as uow:
                uow.perfiles_historicos.upsert(perfil)
                uow.commit()
        except Exception as exc:
            log.warning("no se pudo guardar perfil historico: %s", exc)

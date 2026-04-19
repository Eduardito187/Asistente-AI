from __future__ import annotations

from datetime import datetime
from typing import Callable

from ....domain.shared.normalizacion import NormalizadorTexto
from ....domain.sugerencias_catalogo import SugerenciaCatalogo
from ...ports import UnitOfWork
from .command import RegistrarSugerenciaCatalogoCommand
from .result import RegistrarSugerenciaCatalogoResult


class RegistrarSugerenciaCatalogoHandler:
    """Handler CQRS: upsert idempotente por `nombre_norm`."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(
        self, cmd: RegistrarSugerenciaCatalogoCommand
    ) -> RegistrarSugerenciaCatalogoResult:
        nombre = (cmd.nombre or "").strip()
        if not nombre:
            return RegistrarSugerenciaCatalogoResult(
                sugerencia_id=0, creada=False, veces_solicitado=0
            )
        nombre_norm = NormalizadorTexto.normalizar(nombre)

        with self._uow_factory() as uow:
            existente = uow.sugerencias_catalogo.por_nombre_norm(nombre_norm)
            if existente is not None:
                uow.sugerencias_catalogo.incrementar(nombre_norm)
                uow.commit()
                return RegistrarSugerenciaCatalogoResult(
                    sugerencia_id=existente.id or 0,
                    creada=False,
                    veces_solicitado=existente.veces_solicitado + 1,
                )
            ahora = datetime.utcnow()
            nueva = SugerenciaCatalogo(
                id=None,
                nombre=nombre,
                nombre_norm=nombre_norm,
                categoria_estimada=(cmd.categoria_estimada or None),
                marca_estimada=(cmd.marca_estimada or None),
                veces_solicitado=1,
                primer_contexto_cliente=(cmd.contexto_cliente or None),
                primera_fecha=ahora,
                ultima_fecha=ahora,
            )
            nuevo_id = uow.sugerencias_catalogo.insertar(nueva)
            uow.commit()
            return RegistrarSugerenciaCatalogoResult(
                sugerencia_id=nuevo_id, creada=True, veces_solicitado=1
            )

from __future__ import annotations

from typing import Callable

from ...ports import UnitOfWork
from .query import ObtenerPerfilHistoricoQuery
from .result import ResultadoObtenerPerfilHistorico


class ObtenerPerfilHistoricoHandler:
    """Handler CQRS: lee snapshot historico del cliente."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: ObtenerPerfilHistoricoQuery) -> ResultadoObtenerPerfilHistorico:
        with self._uow_factory() as uow:
            perfil = uow.perfiles_historicos.obtener_por_contacto_hash(q.contacto_hash)
        if perfil is None:
            return ResultadoObtenerPerfilHistorico(encontrado=False, perfil_snapshot={})
        return ResultadoObtenerPerfilHistorico(
            encontrado=True,
            perfil_snapshot=perfil.perfil_snapshot,
            ultima_categoria=perfil.ultima_categoria,
            ultima_marca=perfil.ultima_marca,
            ultima_compra_sku=perfil.ultima_compra_sku,
            visitas=perfil.visitas,
        )

from __future__ import annotations

from typing import Callable

from ...ports import UnitOfWork
from .query import ObtenerPerfilSesionQuery
from .result import ResultadoObtenerPerfilSesion


class ObtenerPerfilSesionHandler:
    """Handler CQRS: lee el perfil de la sesion (o uno vacio)."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, q: ObtenerPerfilSesionQuery) -> ResultadoObtenerPerfilSesion:
        with self._uow_factory() as uow:
            perfil = uow.perfiles_sesion.obtener(q.sesion_id)
        if perfil is None:
            return ResultadoObtenerPerfilSesion(None, None, None, None)
        return ResultadoObtenerPerfilSesion(
            presupuesto_max=perfil.presupuesto_max,
            marca_preferida=perfil.marca_preferida,
            categoria_foco=perfil.categoria_foco,
            uso_declarado=perfil.uso_declarado,
            pulgadas=perfil.pulgadas,
            tipo_panel=perfil.tipo_panel,
            resolucion=perfil.resolucion,
            ultimos_skus_mostrados=perfil.ultimos_skus_mostrados,
            precio_min_mostrado=perfil.precio_min_mostrado,
            precio_max_mostrado=perfil.precio_max_mostrado,
            alternativa_ofrecida=perfil.alternativa_ofrecida,
            subcategoria_foco=perfil.subcategoria_foco,
            genero_declarado=perfil.genero_declarado,
            sku_foco=perfil.sku_foco,
            desired_tier=perfil.desired_tier,
            ram_gb_min=perfil.ram_gb_min,
            gpu_dedicada=perfil.gpu_dedicada,
            ssd_gb_min=perfil.ssd_gb_min,
            nombre_excluye_acum=perfil.nombre_excluye_acum,
            presupuesto_ideal=perfil.presupuesto_ideal,
        )

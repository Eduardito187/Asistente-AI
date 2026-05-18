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
            capacidad_litros_min=perfil.capacidad_litros_min,
            nombre_excluye_acum=perfil.nombre_excluye_acum,
            presupuesto_ideal=perfil.presupuesto_ideal,
            presupuesto_min_buscado=perfil.presupuesto_min_buscado,
            frustracion_count=perfil.frustracion_count,
            ciudad_sesion=perfil.ciudad_sesion,
            refresh_hz_min=perfil.refresh_hz_min,
            bateria_mah_min=perfil.bateria_mah_min,
            camara_mp_min=perfil.camara_mp_min,
            capacidad_kg_min=perfil.capacidad_kg_min,
            potencia_w_min=perfil.potencia_w_min,
            soporta_5g=perfil.soporta_5g,
            sistema_operativo=perfil.sistema_operativo,
            inverter=perfil.inverter,
            no_frost=perfil.no_frost,
            smart_tv=perfil.smart_tv,
            bluetooth_incluido=perfil.bluetooth_incluido,
            nfc=perfil.nfc,
            usb_c=perfil.usb_c,
            hdmi_2_1=perfil.hdmi_2_1,
        )

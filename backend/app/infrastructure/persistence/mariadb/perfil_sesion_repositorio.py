from __future__ import annotations

import json
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from ....domain.perfiles_sesion import PerfilSesion, PerfilSesionRepository
from .mappers import PerfilSesionMapper
from .sql import PerfilSesionSql


class MariaDbPerfilSesionRepository(PerfilSesionRepository):
    """Impl MariaDB del repo de PerfilSesion."""

    def __init__(self, session: Session) -> None:
        self._s = session

    def obtener(self, sesion_id: UUID) -> Optional[PerfilSesion]:
        row = (
            self._s.execute(text(PerfilSesionSql.POR_ID), {"sid": str(sesion_id)})
            .mappings()
            .first()
        )
        return PerfilSesionMapper.from_row(dict(row)) if row else None

    def guardar(self, perfil: PerfilSesion) -> None:
        self._s.execute(
            text(PerfilSesionSql.UPSERT),
            {
                "sid": str(perfil.sesion_id),
                "pmax": perfil.presupuesto_max,
                "marca": perfil.marca_preferida,
                "cat": perfil.categoria_foco,
                "subcat": perfil.subcategoria_foco,
                "sku": perfil.sku_foco,
                "gen": perfil.genero_declarado,
                "tier": perfil.desired_tier,
                "uso": perfil.uso_declarado,
                "pulg": perfil.pulgadas,
                "panel": perfil.tipo_panel,
                "res": perfil.resolucion,
                "ram": perfil.ram_gb_min,
                "gpu": 1 if perfil.gpu_dedicada else None,
                "ssd": perfil.ssd_gb_min,
                "litros_min": perfil.capacidad_litros_min,
                "excluye": perfil.nombre_excluye_acum,
                "pideal": perfil.presupuesto_ideal,
                "pmin_buscado": perfil.presupuesto_min_buscado,
                "frust": perfil.frustracion_count,
                "ciudad": perfil.ciudad_sesion,
                "notas": perfil.notas_usuario,
                "hz_min": perfil.refresh_hz_min,
                "bat_min": perfil.bateria_mah_min,
                "cam_min": perfil.camara_mp_min,
                "s5g": 1 if perfil.soporta_5g else None,
                "so": perfil.sistema_operativo,
                "kg_min": perfil.capacidad_kg_min,
                "pw_min": perfil.potencia_w_min,
                "inverter": 1 if perfil.inverter else None,
                "no_frost": 1 if perfil.no_frost else None,
                "smart_tv": 1 if perfil.smart_tv else None,
                "bluetooth": 1 if perfil.bluetooth_incluido else None,
                "nfc": 1 if perfil.nfc else None,
                "usb_c": 1 if perfil.usb_c else None,
                "hdmi_2_1": 1 if perfil.hdmi_2_1 else None,
            },
        )

    def limpiar(self, sesion_id: UUID) -> None:
        """Limpia campos de búsqueda: categoria, marca, SKU, uso, specs.
        Preserva presupuesto, ciudad, frustracion_count."""
        self._s.execute(text(PerfilSesionSql.LIMPIAR_BUSQUEDA), {"sid": str(sesion_id)})

    _SQL_DOMINIO = {
        "digital":       PerfilSesionSql.LIMPIAR_DOMINIO_DIGITAL,
        "linea_blanca":  PerfilSesionSql.LIMPIAR_DOMINIO_LINEA_BLANCA,
        "tv":            PerfilSesionSql.LIMPIAR_DOMINIO_TV,
    }

    def limpiar_dominio(self, sesion_id: UUID, dominio: str) -> None:
        """Limpia atributos del dominio saliente al cambiar de macro-dominio."""
        sql = self._SQL_DOMINIO.get(dominio)
        if sql:
            self._s.execute(text(sql), {"sid": str(sesion_id)})

    def limpiar_presupuesto_y_marca(self, sesion_id: UUID) -> None:
        """Limpia presupuesto y marca huérfanos cuando el dominio anterior es
        desconocido (categoria_foco era NULL) pero hay contaminación potencial."""
        self._s.execute(
            text(PerfilSesionSql.LIMPIAR_PRESUPUESTO_Y_MARCA), {"sid": str(sesion_id)}
        )

    def obtener_contexto_dominio(self, sesion_id: UUID) -> dict:
        row = (
            self._s.execute(
                text(PerfilSesionSql.OBTENER_CONTEXTO_DOMINIO), {"sid": str(sesion_id)}
            )
            .mappings()
            .first()
        )
        if not row or not row.get("dominio_contexto"):
            return {}
        try:
            return json.loads(row["dominio_contexto"])
        except Exception:
            return {}

    def guardar_contexto_dominio(self, sesion_id: UUID, contexto: dict) -> None:
        self._s.execute(
            text(PerfilSesionSql.GUARDAR_CONTEXTO_DOMINIO),
            {"sid": str(sesion_id), "ctx": json.dumps(contexto, default=str)},
        )

    def registrar_turno(
        self,
        sesion_id: UUID,
        skus_mostrados: Optional[str],
        precio_min: Optional[float],
        precio_max: Optional[float],
    ) -> None:
        self._s.execute(
            text(PerfilSesionSql.REGISTRAR_TURNO),
            {
                "sid": str(sesion_id),
                "skus": skus_mostrados,
                "pmin": precio_min,
                "pmax": precio_max,
            },
        )

    def registrar_alternativa_ofrecida(
        self, sesion_id: UUID, alternativa: str
    ) -> None:
        self._s.execute(
            text(PerfilSesionSql.REGISTRAR_ALTERNATIVA),
            {"sid": str(sesion_id), "alt": alternativa},
        )

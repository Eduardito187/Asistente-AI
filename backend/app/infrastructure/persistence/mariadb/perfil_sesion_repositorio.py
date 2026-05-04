from __future__ import annotations

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
                "excluye": perfil.nombre_excluye_acum,
                "pideal": perfil.presupuesto_ideal,
            },
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

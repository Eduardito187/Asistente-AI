from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID


@dataclass
class PerfilSesion:
    """Agregado PerfilSesion: preferencias declaradas por el cliente durante
    el chat. Usado para pre-filtrar busquedas y evitar preguntar lo mismo
    en cada turno."""

    sesion_id: UUID
    presupuesto_max: Optional[float]
    marca_preferida: Optional[str]
    categoria_foco: Optional[str]
    uso_declarado: Optional[str]
    pulgadas: Optional[float]
    tipo_panel: Optional[str]
    resolucion: Optional[str]
    updated_at: datetime
    ultimos_skus_mostrados: Optional[str] = None
    precio_min_mostrado: Optional[float] = None
    precio_max_mostrado: Optional[float] = None
    alternativa_ofrecida: Optional[str] = None
    subcategoria_foco: Optional[str] = None
    genero_declarado: Optional[str] = None
    sku_foco: Optional[str] = None
    desired_tier: Optional[str] = None
    ram_gb_min: Optional[int] = None
    gpu_dedicada: Optional[bool] = None
    ssd_gb_min: Optional[int] = None
    nombre_excluye_acum: Optional[str] = None  # comma-separated acumulado
    presupuesto_ideal: Optional[float] = None  # techo blando: prefiere no exceder

    @staticmethod
    def vacio(sesion_id: UUID) -> "PerfilSesion":
        return PerfilSesion(
            sesion_id=sesion_id,
            presupuesto_max=None,
            marca_preferida=None,
            categoria_foco=None,
            uso_declarado=None,
            pulgadas=None,
            tipo_panel=None,
            resolucion=None,
            updated_at=datetime.now(timezone.utc),
        )

    def esta_vacio(self) -> bool:
        return not any(
            [
                self.presupuesto_max, self.marca_preferida, self.categoria_foco,
                self.subcategoria_foco, self.uso_declarado, self.pulgadas,
                self.tipo_panel, self.resolucion,
            ]
        )

    @staticmethod
    def _pick(nuevo, viejo):
        return nuevo or viejo

    def fusionar(self, otro: "PerfilSesion") -> "PerfilSesion":
        """Devuelve un nuevo perfil: los campos no nulos de `otro` pisan los de self."""
        p = self._pick
        return PerfilSesion(
            sesion_id=self.sesion_id,
            updated_at=datetime.now(timezone.utc),
            presupuesto_max=p(otro.presupuesto_max, self.presupuesto_max),
            marca_preferida=p(otro.marca_preferida, self.marca_preferida),
            categoria_foco=p(otro.categoria_foco, self.categoria_foco),
            uso_declarado=p(otro.uso_declarado, self.uso_declarado),
            pulgadas=p(otro.pulgadas, self.pulgadas),
            tipo_panel=p(otro.tipo_panel, self.tipo_panel),
            resolucion=p(otro.resolucion, self.resolucion),
            ultimos_skus_mostrados=p(otro.ultimos_skus_mostrados, self.ultimos_skus_mostrados),
            precio_min_mostrado=p(otro.precio_min_mostrado, self.precio_min_mostrado),
            precio_max_mostrado=p(otro.precio_max_mostrado, self.precio_max_mostrado),
            alternativa_ofrecida=p(otro.alternativa_ofrecida, self.alternativa_ofrecida),
            subcategoria_foco=p(otro.subcategoria_foco, self.subcategoria_foco),
            genero_declarado=p(otro.genero_declarado, self.genero_declarado),
            sku_foco=p(otro.sku_foco, self.sku_foco),
            desired_tier=p(otro.desired_tier, self.desired_tier),
            ram_gb_min=p(otro.ram_gb_min, self.ram_gb_min),
            gpu_dedicada=p(otro.gpu_dedicada, self.gpu_dedicada),
            ssd_gb_min=p(otro.ssd_gb_min, self.ssd_gb_min),
            nombre_excluye_acum=p(otro.nombre_excluye_acum, self.nombre_excluye_acum),
            presupuesto_ideal=p(otro.presupuesto_ideal, self.presupuesto_ideal),
        )

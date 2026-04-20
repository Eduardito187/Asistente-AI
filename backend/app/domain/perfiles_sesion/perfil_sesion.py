from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
            updated_at=datetime.utcnow(),
            ultimos_skus_mostrados=None,
            precio_min_mostrado=None,
            precio_max_mostrado=None,
            alternativa_ofrecida=None,
        )

    def esta_vacio(self) -> bool:
        return not any(
            [
                self.presupuesto_max, self.marca_preferida, self.categoria_foco,
                self.uso_declarado, self.pulgadas, self.tipo_panel, self.resolucion,
            ]
        )

    def fusionar(self, otro: "PerfilSesion") -> "PerfilSesion":
        """Devuelve un nuevo perfil: los campos no nulos de `otro` pisan los de self."""
        return PerfilSesion(
            sesion_id=self.sesion_id,
            presupuesto_max=otro.presupuesto_max or self.presupuesto_max,
            marca_preferida=otro.marca_preferida or self.marca_preferida,
            categoria_foco=otro.categoria_foco or self.categoria_foco,
            uso_declarado=otro.uso_declarado or self.uso_declarado,
            pulgadas=otro.pulgadas or self.pulgadas,
            tipo_panel=otro.tipo_panel or self.tipo_panel,
            resolucion=otro.resolucion or self.resolucion,
            updated_at=datetime.utcnow(),
            ultimos_skus_mostrados=otro.ultimos_skus_mostrados or self.ultimos_skus_mostrados,
            precio_min_mostrado=otro.precio_min_mostrado or self.precio_min_mostrado,
            precio_max_mostrado=otro.precio_max_mostrado or self.precio_max_mostrado,
            alternativa_ofrecida=otro.alternativa_ofrecida or self.alternativa_ofrecida,
        )

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ActualizarPerfilSesionCommand:
    """Comando: fusiona los campos no nulos sobre el perfil existente."""

    sesion_id: UUID
    presupuesto_max: Optional[float] = None
    marca_preferida: Optional[str] = None
    categoria_foco: Optional[str] = None
    subcategoria_foco: Optional[str] = None
    sku_foco: Optional[str] = None
    genero_declarado: Optional[str] = None
    desired_tier: Optional[str] = None
    uso_declarado: Optional[str] = None
    pulgadas: Optional[float] = None
    tipo_panel: Optional[str] = None
    resolucion: Optional[str] = None
    ram_gb_min: Optional[int] = None
    gpu_dedicada: Optional[bool] = None

    def tiene_datos(self) -> bool:
        return any(
            [
                self.presupuesto_max, self.marca_preferida, self.categoria_foco,
                self.subcategoria_foco, self.sku_foco, self.genero_declarado,
                self.desired_tier, self.uso_declarado, self.pulgadas,
                self.tipo_panel, self.resolucion, self.ram_gb_min, self.gpu_dedicada,
            ]
        )
